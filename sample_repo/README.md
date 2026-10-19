# CodePilot AI Sample Demo Repository

This sample repository contains realistic software utilities with deliberately introduced bugs for testing and demonstrating CodePilot AI's autonomous bug diagnosis, patch generation, regression testing, and verification pipeline without requiring paid API access.

## Modules

1. **`src/math_engine.py`**:
   - `divide(numerator, denominator)`: Crashes with `ZeroDivisionError` when `denominator == 0`.
   - `compute_moving_averages(data, window)`: Off-by-one edge condition when `window <= 0` or boundary length.

2. **`src/formatter.py`**:
   - `slugify(text)`: Regex metacharacter escape issue when processing special characters.
   - `truncate(text, max_len)`: Boundary indexing bug.

## Running Tests Locally

```bash
pytest -v
```
