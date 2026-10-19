import pytest
from src.formatter import slugify, truncate_text

def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"

def test_truncate_short_string():
    assert truncate_text("Short", 10) == "Short"
