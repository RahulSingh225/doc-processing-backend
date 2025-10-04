from app.operations.base import OperationBase
from typing import Dict, Any
import img2pdf
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('jpg', 'pdf')  # Supports JPG/PNG etc.

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        output_key = f"processed/{inputs['job_id']}.pdf"

        with tempfile.TemporaryDirectory() as tmpdir:
            local_paths = []
            for i, key in enumerate(inputs['file_keys']):
                local_path = os.path.join(tmpdir, f'image_{i}')
                download_from_s3(key, local_path)
                local_paths.append(local_path)

            try:
                pdf_bytes = img2pdf.convert(local_paths)  # Lossless, handles batch
                output_path = os.path.join(tmpdir, 'output.pdf')
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                upload_to_s3(output_path, output_key)
                metadata = {'images': len(local_paths)}
            except Exception as e:
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}