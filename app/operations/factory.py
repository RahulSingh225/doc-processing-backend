from typing import Dict, Type
import importlib
from .base import OperationBase

class OperationFactory:
    _registry: Dict[str, OperationBase] = {}

    @classmethod
    def register(cls, name: str, operation_class: Type[OperationBase]):
        cls._registry[name] = operation_class()

    @classmethod
    def get(cls, name: str) -> OperationBase:
        if name not in cls._registry:
            try:
                module = importlib.import_module(f"app.operations.{name.replace('-', '_')}")
                op_class = getattr(module, 'Operation')
                cls._registry[name] = op_class()
            except (ImportError, AttributeError):
                raise ValueError(f"Operation '{name}' not found")
        return cls._registry[name]