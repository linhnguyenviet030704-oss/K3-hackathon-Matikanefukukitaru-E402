import argparse
import json
import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^(#{2,})\s+(.*\S)\s*$")


def clean_heading(line):
    match = HEADING_RE.match(line)
    if not match:
        return line

    level = len(match.group(1))
    title = match.group(2).strip()
    if level == 4:
        title = re.sub(r"^\d+\.\s*", "", title)
    elif level >= 5:
        title = re.sub(r"^(\d+(?:\.\d+)+)\.?\s+", r"\1 ", title)
    return title


def chunk_file(source_path, output_path):
    source_path = Path(source_path)
    output_path = Path(output_path)
    lines = source_path.read_text(encoding="utf-8-sig").splitlines()

    chapter = chapter_line = ""
    disease = disease_line = ""
    current = None
    chunks = []

    def close_chunk(end_line):
        if not current:
            return
        body = "\n".join(clean_heading(line) for line in current["body"]).strip()
        text_lines = [clean_heading(line) for line in (disease_line, current["section_line"]) if line]
        if body:
            text_lines.append(body)
        text = "\n".join(text_lines)
        chunks.append(
            {
                "id": f"d1_{len(chunks) + 1:04d}",
                "chapter": current["chapter"],
                "disease": current["disease"],
                "section": current["section"],
                "start_line": current["start_line"],
                "end_line": end_line,
                "char_count": len(text),
                "word_count": len(re.findall(r"\S+", text)),
                "utf8_bytes": len(text.encode("utf-8")),
                "text": text,
            }
        )

    for line_no, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            if level in (2, 3, 4):
                close_chunk(line_no - 1)
                current = None
            if level == 2:
                chapter, chapter_line = title, line.strip()
                disease = disease_line = ""
                continue
            if level == 3:
                disease, disease_line = title, line.strip()
                continue
            if level == 4:
                current = {
                    "chapter": chapter,
                    "disease": disease,
                    "section": title,
                    "section_line": line.strip(),
                    "start_line": line_no,
                    "body": [],
                }
                continue

        if current:
            current["body"].append(line)

    close_chunk(len(lines))
    output_path.write_text(
        "\n".join(json.dumps(chunk, ensure_ascii=False) for chunk in chunks) + "\n",
        encoding="utf-8",
    )
    return chunks


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    data_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Chunk data/d1.md by level-4 Markdown headings.")
    parser.add_argument("source", nargs="?", type=Path, default=data_dir / "d1.md")
    parser.add_argument("output", nargs="?", type=Path, default=data_dir / "d1_chunks.jsonl")
    args = parser.parse_args()

    chunks = chunk_file(args.source, args.output)
    largest = max(chunks, key=lambda chunk: chunk["utf8_bytes"], default=None)
    print(f"Wrote {len(chunks)} chunks to {args.output}")
    if largest:
        print(
            "Largest: "
            f'{largest["id"]} | {largest["chapter"]} / {largest["disease"]} / {largest["section"]} '
            f'| {largest["utf8_bytes"]} bytes | {largest["word_count"]} words '
            f'| lines {largest["start_line"]}-{largest["end_line"]}'
        )


if __name__ == "__main__":
    main()
