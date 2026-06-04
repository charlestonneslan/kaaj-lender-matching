"""Extract a YAML draft from a lender PDF.

Reads text from a PDF, dumps a structured template the user fills in.
This is intentionally lightweight, not a full PDF parser. The point is
to give underwriters a starting file to edit rather than typing from
scratch.

Usage:
    python scripts/extract_draft.py lenders/_pdfs/somebank.pdf > lenders/somebank.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path

TEMPLATE = """\
# Draft generated from {pdf_name}. Edit values, then run `python -m app.seed`.
slug: {slug}
name: {name}
contact: # TODO
notes: |
  # TODO summary of the credit box

programs:
  - name: # TODO program/tier name
    priority: 1
    rules:
      - kind: numeric
        field: guarantor.fico
        op: gte
        value: 700
        weight: 5
        hard: true
        message: "FICO {{actual}} below required {{required}}"
      - kind: numeric
        field: business_credit.paynet_score
        op: gte
        value: 650
        weight: 4
        hard: true
        message: "PayNet {{actual}} below required {{required}}"
      - kind: numeric
        field: borrower.years_in_business
        op: gte
        value: 3
        weight: 3
        hard: true
      # TODO state exclusions, industry exclusions, BK rules, amount caps, etc.

# Text extracted from the PDF for reference:
# {snippet}
"""


def extract_text(path: Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        return "(pdfplumber not installed; pip install pdfplumber to enable text extraction)"

    chunks: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def main(pdf_path: str) -> int:
    path = Path(pdf_path)
    if not path.exists():
        print(f"not found: {pdf_path}", file=sys.stderr)
        return 1
    slug = path.stem.lower().replace(" ", "_")
    name = path.stem.replace("_", " ").title()
    text = extract_text(path)
    snippet = "\n# ".join(text.splitlines()[:40])
    print(TEMPLATE.format(pdf_name=path.name, slug=slug, name=name, snippet=snippet))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
