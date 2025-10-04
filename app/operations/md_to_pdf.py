from app.operations.base import OperationBase
from typing import Dict, Any
import markdown
from weasyprint import HTML
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('md', 'pdf')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.pdf"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.md')
            output_path = os.path.join(tmpdir, 'output.pdf')

            download_from_s3(input_key, input_path)
            try:
                with open(input_path, 'r') as f:
                    md_content = f.read()
                html_content = markdown.markdown(md_content, extras=['fenced-code-blocks', 'tables'])  # Extras for better formatting
                HTML(string=html_content).write_pdf(output_path)  # Retains styling
                upload_to_s3(output_path, output_key)
                metadata = {}
            except Exception as e:
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}