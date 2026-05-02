from pathlib import Path
from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .xlsx_parser import parse_xlsx
from .json_parser import parse_json
from .text_parser import parse_text


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".json", ".txt", ".md"}


def parse_file(file_path: str | Path) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return parse_pdf(path)
    if ext == ".docx":
        return parse_docx(path)
    if ext in (".xlsx", ".xls"):
        return parse_xlsx(path)
    if ext == ".json":
        return parse_json(path)
    if ext in (".txt", ".md"):
        return parse_text(path)
    if ext in (".hwp", ".hwpx"):
        raise NotImplementedError(
            "HWP 파서는 v1.1에서 지원 예정입니다. "
            "임시로 hwp 파일을 PDF/Word로 변환 후 업로드하세요."
        )
    raise ValueError(f"지원하지 않는 파일 형식: {ext}")
