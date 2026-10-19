import os
import sys
import json
from pathlib import Path

# Add project root to path
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

from backend.app.services.benchmark_runner import run_benchmarks

def main():
    print("=" * 70)
    print(" CodePilot AI — Benchmark & Evaluation Suite (10+ Fixtures)")
    print("=" * 70)
    print("Executing evaluation across 10 reproducible buggy test fixtures...")
    
    results = run_benchmarks()

    print(f"\nProvider Used: {results['provider']}")
    print(f"Total Fixtures Evaluated: {results['total_fixtures']}")
    print("-" * 70)
    print(f"Bug Localization Accuracy:      {results['localization_accuracy']}%")
    print(f"Valid Patch Rate:               {results['valid_patch_rate']}%")
    print(f"Regression Test Pass Rate:      {results['regression_test_pass_rate']}%")
    print(f"Verified Fix Rate:              {results['verified_fix_rate']}%")
    print(f"False Positive Rate:            {results['false_positive_rate']}%")
    print(f"Median Analysis Duration:       {results['median_duration_seconds']}s")
    print(f"Estimated Cost:                 ${results['estimated_cost_usd']}")
    print("-" * 70)

    print("\nDetailed Per-Fixture Breakdown:")
    for f in results["fixtures"]:
        status = "PASSED" if f["verified_fix"] else "FAILED"
        print(f"  [{status}] {f['fixture_id']}: {f['name']} ({f['file']}) - {f['duration_s']}s")

    # Save results to benchmarks/benchmark_results.json
    out_file = base_dir / "benchmarks" / "benchmark_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nBenchmark metrics saved to: {out_file}")

if __name__ == "__main__":
    main()
