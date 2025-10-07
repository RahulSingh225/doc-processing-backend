import logging
from app.operations.base import OperationBase
from typing import Dict, Any
from pdf2image import convert_from_path
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os
import zipfile

logger = logging.getLogger(__name__)

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('pdf', 'png')  # Outputs ZIP of PNGs

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.zip"

        logger.debug(f"Starting PDF to PNG conversion. Input S3 key: {input_key}")
        logger.debug(f"Output will be stored at: {output_key}")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.pdf')
            zip_path = os.path.join(tmpdir, 'output.zip')

            try:
                logger.debug("Downloading file from S3...")
                download_from_s3(input_key, input_path)
                logger.debug(f"File downloaded to {input_path}")

                logger.debug("Converting PDF to PNG images...")
                images = convert_from_path(
                    input_path,
                    dpi=300,
                    thread_count=4,
                    fmt='png'
                )
                logger.debug(f"Total pages converted: {len(images)}")

                with zipfile.ZipFile(zip_path, 'w') as zf:
                    for i, img in enumerate(images):
                        img_path = os.path.join(tmpdir, f'page_{i+1}.png')
                        img.save(img_path, 'PNG')
                        zf.write(img_path, os.path.basename(img_path))
                        os.remove(img_path)
                        logger.debug(f"Processed and zipped page {i+1}")

                logger.debug("Uploading ZIP to S3...")
                upload_to_s3(zip_path, output_key)
                logger.debug("Upload complete.")

                metadata = {'pages': len(images)}
                logger.info("PDF conversion completed successfully.")
            except Exception as e:
                logger.error(f"Conversion failed: {str(e)}", exc_info=True)
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}
