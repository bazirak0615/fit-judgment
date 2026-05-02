from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .xlsx_parser import parse_xlsx
from .json_parser import parse_json
from .text_parser import parse_text
from .dispatcher import parse_file
from .multi_candidate import load_json_candidates, MAX_CANDIDATES_PER_JSON

__all__ = [
    "parse_pdf",
    "parse_docx",
    "parse_xlsx",
    "parse_json",
    "parse_text",
    "parse_file",
    "load_json_candidates",
    "MAX_CANDIDATES_PER_JSON",
]
