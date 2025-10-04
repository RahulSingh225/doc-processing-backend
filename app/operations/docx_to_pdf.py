from app.operations.base import OperationBase
from typing import Dict, Any
from docx2pdf import convert
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('docx', 'pdf')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.pdf"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.docx')
            output_path = os.path.join(tmpdir, 'output.pdf')

            download_from_s3(input_key, input_path)
            try:
                convert(input_path, output_path)  # Retains formatting via OS tools
                upload_to_s3(output_path, output_key)
                metadata = {}  # Add page count if needed via pypdf
            except Exception as e:
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}