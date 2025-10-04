from app.operations.base import OperationBase
from typing import Dict, Any
import pandas as pd
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('csv', 'xlsx')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}.xlsx"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.xlsx')

            download_from_s3(input_key, input_path)
            try:
                # Handle large CSV: Read all if possible, or chunk and append sheets if too big
                df = pd.read_csv(input_path)
                df.to_excel(output_path, index=False)  # For very large, use ExcelWriter with chunks
                upload_to_s3(output_path, output_key)
                metadata = {'rows': len(df)}
            except Exception as e:
                raise ValueError(f"Conversion failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}