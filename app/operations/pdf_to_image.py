from app.operations.base import OperationBase
from typing import Dict, Any
from pdf2image import convert_from_path
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os
import zipfile

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('pdf', 'png')  # Outputs ZIP of PNGs

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.zip"  # ZIP for multiple images

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.pdf')
            zip_path = os.path.join(tmpdir, 'output.zip')

            download_from_s3(input_key, input_path)
            try:
                images = convert_from_path(input_path, dpi=300, thread_count=4, fmt='png')  # High DPI, threading for large PDFs
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    for i, img in enumerate(images):
                        img_path = os.path.join(tmpdir, f'page_{i+1}.png')
                        img.save(img_path, 'PNG')
                        zf.write(img_path, os.path.basename(img_path))
                        os.remove(img_path)
                upload_to_s3(zip_path, output_key)
                metadata = {'pages': len(images)}
            except Exception as e:
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}