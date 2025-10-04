from abc import ABC, abstractmethod
from typing import Dict, Any

class OperationBase(ABC):
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the operation. Returns {'output_key': str, 'metadata': dict}"""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> tuple:
        pass