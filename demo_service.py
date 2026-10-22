"""
Demo CSV Processing Service.
Used for demonstrating live PR behavioral regression checks.
"""

def parse_csv_lines(value: str) -> list[str]:
    """Parse CSV text and ensure non-empty."""
    lines = value.strip().splitlines()
    assert len(lines) > 0, "Expected non-empty CSV string"
    assert "," in lines[0] or ";" in lines[0] or "\t" in lines[0], "Expected comma, semicolon, or tab delimiter"
    return lines


def process_header(csv_text: str) -> str:
    """Helper that calls parse_csv_lines."""
    lines = parse_csv_lines(csv_text)
    return lines[0].strip()
