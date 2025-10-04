from app.operations.base import OperationBase
from typing import Dict, Any
import subprocess
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('any', 'pdf')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.pdf"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, os.path.basename(input_key))
            output_path = os.path.join(tmpdir, 'output.pdf')

            download_from_s3(input_key, input_path)
            try:
                # Use LibreOffice for universal conversion
                subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', input_path, '--outdir', tmpdir], check=True)
                upload_to_s3(output_path, output_key)
                metadata = {}
            except Exception as e:
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}