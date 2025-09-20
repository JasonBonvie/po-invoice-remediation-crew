from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from markitdown import MarkItDown
import os


class MarkItDownToolInput(BaseModel):
    """Input schema for MarkItDownTool."""
    invoice_file_path: str = Field(..., description="Path to the invoice file to convert to markdown. Supports PDF, Word, Excel, PowerPoint, images, and many other formats.")
    po_file_path: str = Field(..., description="Path to the purchase order (PO) file to convert to markdown. Supports PDF, Word, Excel, PowerPoint, images, and many other formats.")


class MarkItDownTool(BaseTool):
    name: str = "markitdown_converter"
    description: str = (
        "Converts invoice and purchase order (PO) files from various formats (PDF, Word, Excel, PowerPoint, images, etc.) to Markdown format. "
        "Takes both an invoice file and a PO file as input and returns the markdown content of both documents. "
        "Perfect for processing business documents for discrepancy analysis and comparison."
    )
    args_schema: Type[BaseModel] = MarkItDownToolInput

    def _run(self, invoice_file_path: str, po_file_path: str) -> str:
        """
        Convert invoice and PO files to markdown format using the markitdown package.
        
        Args:
            invoice_file_path: Path to the invoice file to convert
            po_file_path: Path to the purchase order file to convert
            
        Returns:
            Markdown content of both files, separated by clear headers
        """
        try:
            # Check if files exist
            if not os.path.exists(invoice_file_path):
                return f"Error: Invoice file not found at path: {invoice_file_path}"
            
            if not os.path.exists(po_file_path):
                return f"Error: PO file not found at path: {po_file_path}"
            
            # Initialize MarkItDown converter
            md = MarkItDown()
            
            # Convert invoice file to markdown
            invoice_result = md.convert(invoice_file_path)
            invoice_content = invoice_result.text_content if invoice_result.text_content else f"Warning: No text content extracted from invoice file {invoice_file_path}"
            
            # Convert PO file to markdown
            po_result = md.convert(po_file_path)
            po_content = po_result.text_content if po_result.text_content else f"Warning: No text content extracted from PO file {po_file_path}"
            
            # Return both contents with clear separation
            return f"""# INVOICE DOCUMENT
{invoice_content}

---

# PURCHASE ORDER DOCUMENT
{po_content}"""
                
        except Exception as e:
            return f"Error converting files to markdown: {str(e)}"
