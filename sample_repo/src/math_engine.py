"""Math calculation engine with intentional boundary and division edge cases."""

def divide(numerator: float, denominator: float) -> float:
    """
    Divide numerator by denominator.
    NOTE: Deliberate bug present — missing guard clause for denominator == 0.
    """
    return numerator / denominator

def calculate_average(values: list) -> float:
    """
    Compute arithmetic mean of a list of numbers.
    NOTE: Deliberate bug present — ZeroDivisionError when list is empty.
    """
    total = sum(values)
    return total / len(values)

def safe_multiply(a: float, b: float) -> float:
    """Safely multiply two numbers."""
    return float(a * b)
