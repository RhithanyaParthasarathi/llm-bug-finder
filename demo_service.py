"""
Demo Service: Real-World Behavioral Regression Scenarios.
Used for demonstrating live PR behavioral regression checks and call-graph reachability.
"""

# ==============================================================================
# Scenario 1: CSV Line Count Validation (Structural Assertion Regression)
# ==============================================================================
def parse_csv_lines(data: str) -> list[str]:
    lines = [line.strip() for line in data.splitlines() if line.strip()]
    assert len(lines) > 0, "Expected at least 1 line"
    #assert len(lines) >= 2, "Expected at least 2 lines for CSV structure" #ai change
    return lines


def process_header(csv_text: str) -> str:
    """Downstream caller for Scenario 1."""
    lines = parse_csv_lines(csv_text)
    return lines[0].strip()


# ==============================================================================
# Scenario 2: Discount Rate Calculator (Boundary Clamping Regression)
# ==============================================================================
def calculate_discount(price: float, rate: float) -> float:
    """Applies discount rate (0.0 to 1.0). Rejects negative rates or over 1.0."""
    if rate < 0.0 or rate > 1.0:
        return price
    #if rate > 1.0: return price  # Simulating AI refactor: AI dropped rate < 0.0 check
    return price * (1.0 - rate)


def checkout_total(cart_price: float, promo_rate: float) -> float:
    """Downstream caller for Scenario 2."""
    return calculate_discount(cart_price, promo_rate)


# ==============================================================================
# Scenario 3: Score Clamping Utility (Numeric Guard Drop Regression)
# ==============================================================================
def clamp_score(score: int, max_val: int = 100) -> int:
    """Clamps a player's score between 0 and max_val."""
    if score < 0:
        return 0
    # pass  # Simulating AI refactor: AI dropped if score < 0: return 0 check
    if score > max_val:
        return max_val
    return score


def render_leaderboard_entry(raw_score: int) -> str:
    """Downstream caller for Scenario 3."""
    final_score = clamp_score(raw_score)
    return f"Player Score: {final_score}"
