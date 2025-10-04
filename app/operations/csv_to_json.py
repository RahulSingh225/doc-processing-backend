from app.operations.base import OperationBase
from typing import Dict, Any
import pandas as pd
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('csv', 'json')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.json')

            download_from_s3(input_key, input_path)
            try:
                # Handle large CSV with chunks
                chunks = pd.read_csv(input_path, chunksize=10000)
                first = True
                for chunk in chunks:
                    chunk.to_json(output_path, orient='records', lines=True, mode='a' if not first else 'w')
                    first = False
                upload_to_s3(output_path, output_key)
                metadata = {}
            except Exception as e:
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}