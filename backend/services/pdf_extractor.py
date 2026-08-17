"""
PDF Extraction Service for PaperSense AI

Validates, reads, and extracts metadata from PDF files.
Prepares PDFs safely for downstream AI analysis services.
"""

from typing import Optional, Tuple
from pydantic import BaseModel
import io


class PDFMetadata(BaseModel):
    """Extracted PDF metadata."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    page_count: int = 0
    is_encrypted: bool = False


class PDFExtractionResult(BaseModel):
    """Result of PDF extraction and validation."""
    success: bool
    pdf_bytes: Optional[bytes] = None
    metadata: PDFMetadata
    error: Optional[str] = None


def is_pdf(file_bytes: bytes) -> bool:
    """
    Validate that the input is a PDF by checking the magic bytes.
    
    Args:
        file_bytes: Raw file bytes to validate
        
    Returns:
        True if file starts with PDF magic bytes, False otherwise
    """
    if not file_bytes or len(file_bytes) < 4:
        return False
    
    # PDF files start with %PDF magic bytes
    return file_bytes[:4] == b"%PDF"


def extract_metadata(file_bytes: bytes) -> Tuple[PDFMetadata, Optional[str]]:
    """
    Extract metadata from PDF bytes.
    
    Args:
        file_bytes: Raw PDF bytes
        
    Returns:
        Tuple of (PDFMetadata, error_message)
        error_message is None if successful
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return PDFMetadata(), "pypdf library not installed. Install with: pip install pypdf"
    
    metadata = PDFMetadata()
    
    try:
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)
        
        # Check if PDF is encrypted
        if reader.is_encrypted:
            metadata.is_encrypted = True
            # pypdf handles encrypted PDFs that don't require a password
            try:
                reader.pages  # This will trigger decryption attempt
            except Exception:
                return metadata, "PDF is password-protected and cannot be read"
        
        # Get page count
        metadata.page_count = len(reader.pages)
        
        # Extract document information
        if reader.metadata:
            metadata.title = reader.metadata.get("/Title", None)
            metadata.author = reader.metadata.get("/Author", None)
            metadata.subject = reader.metadata.get("/Subject", None)
            metadata.creator = reader.metadata.get("/Creator", None)
            metadata.producer = reader.metadata.get("/Producer", None)
        
        return metadata, None
    
    except Exception as e:
        return metadata, f"Failed to extract metadata: {str(e)}"


def extract_pdf(file_bytes: bytes, filename: Optional[str] = None) -> PDFExtractionResult:
    """
    Validate, read, and extract metadata from a PDF file.
    
    Args:
        file_bytes: Raw bytes of the PDF file
        filename: Optional filename for additional context
        
    Returns:
        PDFExtractionResult with success status, PDF bytes, metadata, and error info
    """
    # Validate input
    if not file_bytes:
        return PDFExtractionResult(
            success=False,
            metadata=PDFMetadata(),
            error="No file bytes provided"
        )
    
    # Check PDF format
    if not is_pdf(file_bytes):
        return PDFExtractionResult(
            success=False,
            metadata=PDFMetadata(),
            error="File is not a valid PDF (invalid magic bytes)"
        )
    
    # Extract metadata
    metadata, metadata_error = extract_metadata(file_bytes)
    
    # Check for critical errors
    if metadata_error and "password-protected" in metadata_error.lower():
        return PDFExtractionResult(
            success=False,
            metadata=metadata,
            error=metadata_error
        )
    
    # Check for empty PDF
    if metadata.page_count == 0:
        return PDFExtractionResult(
            success=False,
            metadata=metadata,
            error="PDF has no pages (empty file)"
        )
    
    # Success: return PDF bytes and metadata
    return PDFExtractionResult(
        success=True,
        pdf_bytes=file_bytes,
        metadata=metadata,
        error=metadata_error  # Include non-critical warnings
    )


def extract_pdf_from_file(file_path: str) -> PDFExtractionResult:
    """
    Extract PDF from a file path.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        PDFExtractionResult
    """
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        
        return extract_pdf(file_bytes, filename=file_path)
    
    except FileNotFoundError:
        return PDFExtractionResult(
            success=False,
            metadata=PDFMetadata(),
            error=f"File not found: {file_path}"
        )
    except IOError as e:
        return PDFExtractionResult(
            success=False,
            metadata=PDFMetadata(),
            error=f"Error reading file: {str(e)}"
        )
