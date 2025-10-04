from app.operations.base import OperationBase
from typing import Dict, Any
from pypdf import PdfMerger
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('pdf', 'pdf')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        output_key = f"processed/{inputs['job_id']}.pdf"

        with tempfile.TemporaryDirectory() as tmpdir:
            local_paths = []
            for i, key in enumerate(inputs['file_keys']):
                local_path = os.path.join(tmpdir, f'input_{i}.pdf')
                download_from_s3(key, local_path)
                local_paths.append(local_path)

            try:
                merger = PdfMerger()
                for path in local_paths:
                    merger.append(path)
                output_path = os.path.join(tmpdir, 'output.pdf')
                merger.write(output_path)
                merger.close()
                upload_to_s3(output_path, output_key)
                metadata = {'files_merged': len(local_paths)}
            except Exception as e:
                raise ValueError(f"Merge failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}