from app.operations.base import OperationBase
from typing import Dict, Any
import pandas as pd
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('json', 'csv')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.csv"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.json')
            output_path = os.path.join(tmpdir, 'output.csv')

            download_from_s3(input_key, input_path)
            try:
                # Handle large JSON with chunks (assume list of dicts)
                chunks = pd.read_json(input_path, lines=True, chunksize=10000)  # For large files
                first = True
                for chunk in chunks:
                    chunk.to_csv(output_path, mode='a' if not first else 'w', index=False)
                    first = False
                upload_to_s3(output_path, output_key)
                metadata = {}
            except Exception as e:
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}