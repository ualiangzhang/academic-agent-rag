import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

CONTRACTS = Path(__file__).resolve().parents[2] / "configs" / "contracts"
VECTORS = Path(__file__).resolve().parents[2] / "configs" / "test_vectors"

TOOL_TO_SCHEMA = {
    "rag.retrieve": CONTRACTS / "rag.retrieve.schema.json",
    "papers.search": CONTRACTS / "papers.search.schema.json",
    "papers.fetch": CONTRACTS / "papers.fetch.schema.json",
    "notes.read": CONTRACTS / "notes.read.schema.json",
    "notes.write": CONTRACTS / "notes.write.schema.json",
    "db.query": CONTRACTS / "db.query.schema.json",
}

VECTORS_MAP = {
    "rag.retrieve": VECTORS / "rag.retrieve.jsonl",
    "papers.search": VECTORS / "papers.search.jsonl",
    "papers.fetch": VECTORS / "papers.fetch.jsonl",
    "notes.read": VECTORS / "notes.read.jsonl",
    "notes.write": VECTORS / "notes.write.jsonl",
    "db.query": VECTORS / "db.query.jsonl",
}


def main() -> int:
    failures = 0
    for tool, schema_path in TOOL_TO_SCHEMA.items():
        schema = json.loads(schema_path.read_text())
        validator = Draft202012Validator(schema)
        vector_path = VECTORS_MAP[tool]
        for line in vector_path.read_text().splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if errors:
                print(f"[FAIL] {tool} vector invalid: {errors[0].message}")
                failures += 1
            else:
                print(f"[OK]   {tool} vector valid")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
