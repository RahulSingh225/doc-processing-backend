from .operations.factory import OperationFactory
from .operations.pdf_to_docx import Operation as PdfToDocx
# ... Import others ...

OperationFactory.register("pdf-to-docx", PdfToDocx)
# Register all operations similarly