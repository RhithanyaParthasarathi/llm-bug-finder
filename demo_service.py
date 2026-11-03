"""
Demo CSV Processing Service.
Used for demonstrating live PR behavioral regression checks.
"""

def parse_csv_lines(data: str) -> list[str]:
    lines = [line.strip() for line in data.splitlines() if line.strip()]
    # To this (simulating an AI assistant "optimizing" or tightening constraints):
    assert len(lines) >= 2, "Expected at least 2 lines for CSV structure"
    return lines


def process_header(csv_text: str) -> str:
    """Helper that calls parse_csv_lines."""
    lines = parse_csv_lines(csv_text)
    return lines[0].strip()
