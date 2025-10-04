from app.operations.base import OperationBase
from typing import Dict, Any
from pypdf import PdfReader, PdfWriter
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os
import zipfile

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('pdf', 'zip')  # ZIP of split PDFs

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.zip"  # Per-page split

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.pdf')
            zip_path = os.path.join(tmpdir, 'output.zip')

            download_from_s3(input_key, input_path)
            try:
                reader = PdfReader(input_path)
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    for i, page in enumerate(reader.pages):
                        writer = PdfWriter()
                        writer.add_page(page)
                        split_path = os.path.join(tmpdir, f'page_{i+1}.pdf')
                        with open(split_path, 'wb') as f:
                            writer.write(f)
                        zf.write(split_path, os.path.basename(split_path))
                        os.remove(split_path)
                upload_to_s3(zip_path, output_key)
                metadata = {'pages': len(reader.pages)}
            except Exception as e:
                raise ValueError(f"Split failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}