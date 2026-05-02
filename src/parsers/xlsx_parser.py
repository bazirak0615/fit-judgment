import pandas as pd
from pathlib import Path


def parse_xlsx(file_path: str | Path) -> str:
    sheets = pd.read_excel(file_path, sheet_name=None, dtype=str)
    parts = []
    for sheet_name, df in sheets.items():
        parts.append(f"### Sheet: {sheet_name}")
        df = df.fillna("")
        parts.append(df.to_csv(index=False, sep="\t"))
    return "\n\n".join(parts)
