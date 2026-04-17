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

    # Track emitted comment IDs across all paragraphs so each comment renders
    # exactly once. Word anchors a comment at both commentRangeStart (first
    # paragraph of the range) and commentReference (last), which would
    # otherwise duplicate multi-paragraph comments in the output.
    emitted_cids: set = set()
    paragraphs = []
    for p in body.iter(f'{{{NS["w"]}}}p'):
        text_parts = []
        for r in p.iter(f'{{{NS["w"]}}}r'):
            for t in r.iter(f'{{{NS["w"]}}}t'):
                if t.text:
                    text_parts.append(t.text)
        text = "".join(text_parts)

        para_comments = []
        for ref in p.iter(f'{{{NS["w"]}}}commentRangeStart'):
            cid = ref.get(f'{{{NS["w"]}}}id')
            if cid in comments and cid not in emitted_cids:
                para_comments.append(comments[cid])
                emitted_cids.add(cid)
        for ref in p.iter(f'{{{NS["w"]}}}commentReference'):
            cid = ref.get(f'{{{NS["w"]}}}id')
            if cid in comments and cid not in emitted_cids:
                para_comments.append(comments[cid])
                emitted_cids.add(cid)

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


def count_source_words(zip_file: zipfile.ZipFile) -> int:
    """Count words in all w:t elements across document.xml (body only)."""
    try:
        xml = zip_file.read("word/document.xml")
    except KeyError:
        return 0
    root = ET.fromstring(xml)
    body = root.find("w:body", NS)
    if body is None:
        return 0
    words = 0
    for t in body.iter(f'{{{NS["w"]}}}t'):
        if t.text:
            words += len(t.text.split())
    return words


def has_text_boxes(zip_file: zipfile.ZipFile) -> int:
    """Return count of text boxes (w:txbxContent) in document body."""
    try:
        xml = zip_file.read("word/document.xml")
    except KeyError:
        return 0
    root = ET.fromstring(xml)
    return sum(1 for _ in root.iter(f'{{{NS["w"]}}}txbxContent'))


def has_notes(zip_file: zipfile.ZipFile) -> tuple[bool, bool]:
    """Return (has_footnotes, has_endnotes) by checking zip contents."""
    names = set(zip_file.namelist())
    return ("word/footnotes.xml" in names, "word/endnotes.xml" in names)


def count_output_words(md_text: str) -> int:
    """Count words in markdown output, stripping markdown syntax characters."""
    # Strip common markdown syntax so we compare prose-to-prose
    import re
    stripped = re.sub(r"[#>|*_`\-]", " ", md_text)
    return len(stripped.split())


def build_report(
    source_path: Path,
    data: dict,
    md_output: str,
    source_words: int,
    text_box_count: int,
    has_footnotes: bool,
    has_endnotes: bool,
) -> tuple[str, bool]:
    """Build a human-readable conversion report. Returns (report, passed)."""
    output_words = count_output_words(md_output)
    word_coverage = (output_words / source_words * 100) if source_words > 0 else 100.0

    md_comment_count = md_output.count("> **[")
    md_table_count = md_output.count("### Table ")

    source_comment_count = data["comment_count"]
    source_table_count = len(data["tables"])

    # Pass criteria
    word_pass = word_coverage >= 95.0
    comment_pass = md_comment_count == source_comment_count
    table_pass = md_table_count == source_table_count

    passed = word_pass and comment_pass and table_pass

    def mark(b: bool) -> str:
        return "✅" if b else "❌"

    lines = [
        f"== Conversion Report: {source_path.name} ==",
        f"  Words:     {source_words:,} → {output_words:,}    ({word_coverage:.1f}%)   {mark(word_pass)}",
        f"  Comments:  {source_comment_count} → {md_comment_count}               {mark(comment_pass)}",
        f"  Tables:    {source_table_count} → {md_table_count}               {mark(table_pass)}",
        f"  Text boxes: {text_box_count} in source    {'⚠️  (skipped by converter)' if text_box_count else '✅'}",
        f"  Footnotes:  {'present' if has_footnotes else 'none'} in source    {'⚠️  (skipped)' if has_footnotes else '✅'}",
        f"  Endnotes:   {'present' if has_endnotes else 'none'} in source    {'⚠️  (skipped)' if has_endnotes else '✅'}",
        "",
        f"  Result: {'PASS' if passed else 'FAIL'}",
    ]
    return "\n".join(lines), passed


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
    md_output = to_markdown(data)

    # Gather source-side metrics for the conversion report
    with zipfile.ZipFile(path) as zf:
        source_words = count_source_words(zf)
        text_box_count = has_text_boxes(zf)
        footnotes_present, endnotes_present = has_notes(zf)

    report, passed = build_report(
        source_path=path,
        data=data,
        md_output=md_output,
        source_words=source_words,
        text_box_count=text_box_count,
        has_footnotes=footnotes_present,
        has_endnotes=endnotes_present,
    )
    print(report, file=sys.stderr)

    if "--markdown" in sys.argv:
        print(md_output)
    else:
        print(json.dumps(data, indent=2))

    if not passed:
        sys.exit(2)
