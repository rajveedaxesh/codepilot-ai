import pytest
from src.math_engine import divide, calculate_average, safe_multiply

def test_divide_valid_numbers():
    assert divide(10.0, 2.0) == 5.0
    assert divide(-9.0, 3.0) == -3.0

def test_safe_multiply():
    assert safe_multiply(4.0, 2.5) == 10.0
