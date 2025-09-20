from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import boto3
import os
import json
from botocore.exceptions import ClientError, NoCredentialsError
import tempfile
import uuid


class TextractToolInput(BaseModel):
    """Input schema for TextractTool."""
    invoice_file_path: str = Field(..., description="Path to the invoice file to analyze. Supports PDF, PNG, JPG, TIFF formats.")
    po_file_path: str = Field(..., description="Path to the purchase order file to analyze. Supports PDF, PNG, JPG, TIFF formats.")
    aws_region: str = Field(default="us-east-1", description="AWS region for Textract service (default: us-east-1)")
    s3_bucket: str = Field(default="", description="Optional S3 bucket name for document storage. If not provided, will use temporary S3 bucket.")


class TextractTool(BaseTool):
    name: str = "textract_document_analyzer"
    description: str = (
        "Analyzes invoice and purchase order documents using Amazon Textract to extract structured data "
        "including text, tables, forms, and key-value pairs. Preserves document structure and formatting "
        "much better than basic OCR. Returns detailed analysis with tables, forms, and text content "
        "organized by document sections."
    )
    args_schema: Type[BaseModel] = TextractToolInput

    def _run(self, invoice_file_path: str, po_file_path: str, aws_region: str = "us-east-1", s3_bucket: str = "") -> str:
        """
        Analyze invoice and PO documents using Amazon Textract.
        
        Args:
            invoice_file_path: Path to the invoice file
            po_file_path: Path to the purchase order file
            aws_region: AWS region for Textract service
            s3_bucket: Optional S3 bucket name
            
        Returns:
            Structured analysis of both documents with preserved formatting
        """
        try:
            # Check if files exist
            if not os.path.exists(invoice_file_path):
                return f"Error: Invoice file not found at path: {invoice_file_path}"
            
            if not os.path.exists(po_file_path):
                return f"Error: PO file not found at path: {po_file_path}"
            
            # Initialize AWS clients
            try:
                textract = boto3.client('textract', region_name=aws_region)
                s3 = boto3.client('s3', region_name=aws_region)
            except NoCredentialsError:
                return "Error: AWS credentials not found. Please configure your AWS credentials."
            except Exception as e:
                return f"Error initializing AWS clients: {str(e)}"
            
            # Handle S3 bucket
            if not s3_bucket:
                s3_bucket = f"textract-temp-{uuid.uuid4().hex[:8]}"
                try:
                    s3.create_bucket(Bucket=s3_bucket)
                except ClientError as e:
                    if e.response['Error']['Code'] != 'BucketAlreadyOwnedByYou':
                        return f"Error creating S3 bucket: {str(e)}"
            
            # Upload files to S3
            invoice_s3_key = f"invoice_{uuid.uuid4().hex[:8]}.pdf"
            po_s3_key = f"po_{uuid.uuid4().hex[:8]}.pdf"
            
            try:
                s3.upload_file(invoice_file_path, s3_bucket, invoice_s3_key)
                s3.upload_file(po_file_path, s3_bucket, po_s3_key)
            except ClientError as e:
                return f"Error uploading files to S3: {str(e)}"
            
            # Analyze documents with Textract
            try:
                # Analyze invoice
                invoice_response = textract.analyze_document(
                    Document={'S3Object': {'Bucket': s3_bucket, 'Name': invoice_s3_key}},
                    FeatureTypes=['TABLES', 'FORMS']
                )
                
                # Analyze PO
                po_response = textract.analyze_document(
                    Document={'S3Object': {'Bucket': s3_bucket, 'Name': po_s3_key}},
                    FeatureTypes=['TABLES', 'FORMS']
                )
                
            except ClientError as e:
                return f"Error analyzing documents with Textract: {str(e)}"
            
            # Process the responses
            invoice_analysis = self._process_textract_response(invoice_response, "INVOICE")
            po_analysis = self._process_textract_response(po_response, "PURCHASE ORDER")
            
            # Clean up S3 files
            try:
                s3.delete_object(Bucket=s3_bucket, Key=invoice_s3_key)
                s3.delete_object(Bucket=s3_bucket, Key=po_s3_key)
                if s3_bucket.startswith("textract-temp-"):
                    s3.delete_bucket(Bucket=s3_bucket)
            except ClientError:
                pass  # Ignore cleanup errors
            
            # Return structured analysis
            return f"""# INVOICE DOCUMENT ANALYSIS
{invoice_analysis}

---

# PURCHASE ORDER DOCUMENT ANALYSIS
{po_analysis}"""
                
        except Exception as e:
            return f"Error processing documents with Textract: {str(e)}"
    
    def _process_textract_response(self, response: dict, doc_type: str) -> str:
        """
        Process Textract response to extract structured information.
        
        Args:
            response: Textract API response
            doc_type: Type of document (INVOICE or PURCHASE ORDER)
            
        Returns:
            Formatted markdown content
        """
        blocks = response.get('Blocks', [])
        
        # Organize blocks by type
        text_blocks = [b for b in blocks if b['BlockType'] == 'LINE']
        table_blocks = [b for b in blocks if b['BlockType'] == 'TABLE']
        cell_blocks = [b for b in blocks if b['BlockType'] == 'CELL']
        key_value_blocks = [b for b in blocks if b['BlockType'] == 'KEY_VALUE_SET']
        
        result = []
        
        # Add document header
        result.append(f"## {doc_type} Document Analysis\n")
        
        # Process key-value pairs (forms)
        if key_value_blocks:
            result.append("### Key-Value Pairs (Forms)")
            result.append("")
            
            # Group key-value pairs
            key_value_pairs = self._extract_key_value_pairs(blocks, key_value_blocks)
            for key, value in key_value_pairs.items():
                result.append(f"**{key}:** {value}")
            result.append("")
        
        # Process tables
        if table_blocks:
            result.append("### Tables")
            result.append("")
            
            for table_block in table_blocks:
                table_content = self._extract_table_content(blocks, table_block, cell_blocks)
                if table_content:
                    result.append(table_content)
                    result.append("")
        
        # Process remaining text
        if text_blocks:
            result.append("### Text Content")
            result.append("")
            
            # Group text by spatial proximity
            text_content = self._extract_text_content(blocks, text_blocks)
            result.append(text_content)
        
        return '\n'.join(result)
    
    def _extract_key_value_pairs(self, blocks: list, key_value_blocks: list) -> dict:
        """Extract key-value pairs from form blocks."""
        key_value_pairs = {}
        
        # Create block lookup
        block_map = {block['Id']: block for block in blocks}
        
        for kv_block in key_value_blocks:
            if kv_block.get('EntityTypes') == ['KEY']:
                key_text = self._get_text_from_block(kv_block, block_map)
                value_text = ""
                
                # Find associated value
                if 'Relationships' in kv_block:
                    for relationship in kv_block['Relationships']:
                        if relationship['Type'] == 'VALUE':
                            for value_id in relationship['Ids']:
                                value_block = block_map.get(value_id)
                                if value_block and value_block.get('EntityTypes') == ['VALUE']:
                                    value_text = self._get_text_from_block(value_block, block_map)
                                    break
                
                if key_text and value_text:
                    key_value_pairs[key_text] = value_text
        
        return key_value_pairs
    
    def _extract_table_content(self, blocks: list, table_block: dict, cell_blocks: list) -> str:
        """Extract table content and format as markdown table."""
        # Create block lookup
        block_map = {block['Id']: block for block in blocks}
        
        # Get cells for this table
        table_cells = []
        if 'Relationships' in table_block:
            for relationship in table_block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for cell_id in relationship['Ids']:
                        cell_block = block_map.get(cell_id)
                        if cell_block and cell_block['BlockType'] == 'CELL':
                            table_cells.append(cell_block)
        
        if not table_cells:
            return ""
        
        # Sort cells by row and column
        table_cells.sort(key=lambda x: (x.get('RowIndex', 0), x.get('ColumnIndex', 0)))
        
        # Build table
        max_row = max(cell.get('RowIndex', 0) for cell in table_cells)
        max_col = max(cell.get('ColumnIndex', 0) for cell in table_cells)
        
        # Create table grid
        table_grid = [[None for _ in range(max_col + 1)] for _ in range(max_row + 1)]
        
        for cell in table_cells:
            row = cell.get('RowIndex', 0) - 1
            col = cell.get('ColumnIndex', 0) - 1
            cell_text = self._get_text_from_block(cell, block_map)
            table_grid[row][col] = cell_text
        
        # Format as markdown table
        if not table_grid or not table_grid[0]:
            return ""
        
        markdown_table = []
        for i, row in enumerate(table_grid):
            # Fill None values with empty strings
            row = [cell or "" for cell in row]
            markdown_table.append("| " + " | ".join(row) + " |")
            
            # Add header separator after first row
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(row)) + " |"
                markdown_table.append(separator)
        
        return '\n'.join(markdown_table)
    
    def _extract_text_content(self, blocks: list, text_blocks: list) -> str:
        """Extract and organize text content."""
        # Sort text blocks by reading order (top to bottom, left to right)
        text_blocks.sort(key=lambda x: (x.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0), 
                                       x.get('Geometry', {}).get('BoundingBox', {}).get('Left', 0)))
        
        text_lines = []
        for block in text_blocks:
            text = block.get('Text', '').strip()
            if text:
                text_lines.append(text)
        
        return '\n'.join(text_lines)
    
    def _get_text_from_block(self, block: dict, block_map: dict) -> str:
        """Get text content from a block, including child blocks."""
        text_parts = []
        
        if 'Text' in block:
            text_parts.append(block['Text'])
        
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        child_block = block_map.get(child_id)
                        if child_block and child_block['BlockType'] == 'WORD':
                            text_parts.append(child_block.get('Text', ''))
        
        return ' '.join(text_parts).strip()
