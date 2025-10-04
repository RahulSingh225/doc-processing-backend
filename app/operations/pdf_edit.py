from app.operations.base import OperationBase
from typing import Dict, Any
from pypdf import PdfReader, PdfWriter
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('pdf', 'pdf')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.pdf"
        # Options example: {'pages_order': [2,1,3], 'remove_pages': [4]} – assume in inputs['options']
        options = inputs.get('options', {})

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.pdf')
            output_path = os.path.join(tmpdir, 'output.pdf')

            download_from_s3(input_key, input_path)
            try:
                reader = PdfReader(input_path)
                writer = PdfWriter()
                pages = list(range(len(reader.pages)))
                # Remove pages
                remove = options.get('remove_pages', [])
                pages = [p for p in pages if p+1 not in remove]  # 1-indexed
                # Rearrange
                order = options.get('pages_order', pages)
                for idx in order:
                    writer.add_page(reader.pages[idx-1])  # 0-indexed
                # Add pages? For add, assume from other files, but for basic, skip or extend if needed
                with open(output_path, 'wb') as f:
                    writer.write(f)
                upload_to_s3(output_path, output_key)
                metadata = {'pages': len(writer.pages)}
            except Exception as e:
                raise ValueError(f"Edit failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}