#!/usr/bin/env python3
"""Extract body text and comments from a .docx file.

Usage:
    python extract_docx.py <path-to-docx>              # JSON to stdout
    python extract_docx.py <path-to-docx> --markdown    # Markdown with inline comments
"""

import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def extract_comments(zip_file: zipfile.ZipFile) -> dict:
    """Parse word/comments.xml → {comment_id: {author, date, text}}"""
    try:
        xml = zip_file.read("word/comments.xml")
    except KeyError:
        return {}

    root = ET.fromstring(xml)
    comments = {}
    for c in root.findall("w:comment", NS):
        cid = c.get(f'{{{NS["w"]}}}id')
        author = c.get(f'{{{NS["w"]}}}author', "Unknown")
        date = c.get(f'{{{NS["w"]}}}date', "")
        # Comment text is in w:p/w:r/w:t elements within the comment
        text_parts = []
        for t in c.iter(f'{{{NS["w"]}}}t'):
            if t.text:
                text_parts.append(t.text)
        comments[cid] = {
            "author": author,
            "date": date,
            "text": " ".join(text_parts),
        }
    return comments


def extract_body(zip_file: zipfile.ZipFile, comments: dict) -> list:
    """Parse word/document.xml → list of paragraph dicts with attached comments."""
    xml = zip_file.read("word/document.xml")
    root = ET.fromstring(xml)

    body = root.find("w:body", NS)
    if body is None:
        return []

    # First pass: find which comment IDs are anchored in which paragraphs
    # commentRangeStart has w:id attribute matching comment ID
    paragraphs = []
    for p in body.iter(f'{{{NS["w"]}}}p'):
        # Extract text
        text_parts = []
        for r in p.iter(f'{{{NS["w"]}}}r'):
            for t in r.iter(f'{{{NS["w"]}}}t'):
                if t.text:
                    text_parts.append(t.text)
        text = "".join(text_parts)

        # Find comment references in this paragraph
        para_comments = []
        for ref in p.iter(f'{{{NS["w"]}}}commentRangeStart'):
            cid = ref.get(f'{{{NS["w"]}}}id')
            if cid in comments:
                para_comments.append(comments[cid])
        # Also check for commentReference (sometimes used instead of range)
        for ref in p.iter(f'{{{NS["w"]}}}commentReference'):
            cid = ref.get(f'{{{NS["w"]}}}id')
            if cid in comments and comments[cid] not in para_comments:
                para_comments.append(comments[cid])

        if text.strip() or para_comments:
            paragraphs.append({"text": text, "comments": para_comments})

    return paragraphs


def extract_tables(zip_file: zipfile.ZipFile) -> list:
    """Extract tables from document body."""
    xml = zip_file.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find("w:body", NS)
    if body is None:
        return []

    tables = []
    for tbl in body.iter(f'{{{NS["w"]}}}tbl'):
        rows = []
        for tr in tbl.iter(f'{{{NS["w"]}}}tr'):
            cells = []
            for tc in tr.iter(f'{{{NS["w"]}}}tc'):
                cell_text = []
                for t in tc.iter(f'{{{NS["w"]}}}t'):
                    if t.text:
                        cell_text.append(t.text)
                cells.append(" ".join(cell_text))
            rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def to_json(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        comments = extract_comments(zf)
        paragraphs = extract_body(zf, comments)
        tables = extract_tables(zf)
    return {
        "file": str(path.name),
        "paragraphs": paragraphs,
        "tables": tables,
        "comment_count": len(comments),
    }


def to_markdown(data: dict) -> str:
    lines = [f"# {data['file']}", f"_({data['comment_count']} comments extracted)_\n"]

    for p in data["paragraphs"]:
        text = p["text"].strip()
        if text:
            lines.append(text)
        for c in p["comments"]:
            author = c["author"]
            comment_text = c["text"]
            date = c.get("date", "")
            date_str = f" ({date[:10]})" if date else ""
            lines.append(f"> **[{author}]{date_str}:** {comment_text}")
        if text or p["comments"]:
            lines.append("")

    if data["tables"]:
        lines.append("---\n## Tables\n")
        for i, table in enumerate(data["tables"], 1):
            lines.append(f"### Table {i}\n")
            if table:
                # Header row
                lines.append("| " + " | ".join(table[0]) + " |")
                lines.append("| " + " | ".join(["---"] * len(table[0])) + " |")
                for row in table[1:]:
                    # Pad row to match header width
                    padded = row + [""] * (len(table[0]) - len(row))
                    lines.append("| " + " | ".join(padded) + " |")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.docx> [--markdown]", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    data = to_json(path)
    if "--markdown" in sys.argv:
        print(to_markdown(data))
    else:
        print(json.dumps(data, indent=2))
