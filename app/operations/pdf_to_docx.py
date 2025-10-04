from app.operations.base import OperationBase
from typing import Dict, Any
from pdf2docx import Converter
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('pdf', 'docx')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]  # Single file for this op
        output_key = f"processed/{inputs['job_id']}.docx"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.pdf')
            output_path = os.path.join(tmpdir, 'output.docx')

            download_from_s3(input_key, input_path)
            try:
                cv = Converter(input_path)
                cv.convert(output_path, multi_processing=True, cpu_count=os.cpu_count())  # Multi-processing for large files
                cv.close()
                upload_to_s3(output_path, output_key)
                metadata = {'pages': cv.pages_count if hasattr(cv, 'pages_count') else 0}
            except Exception as e:
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}