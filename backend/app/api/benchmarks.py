from typing import Dict, Any
from fastapi import APIRouter
from backend.app.services.benchmark_runner import run_benchmarks, BENCHMARK_FIXTURES_META

router = APIRouter(prefix="/benchmarks", tags=["Evaluation & Benchmarks"])

@router.get("/fixtures")
def list_benchmark_fixtures():
    """List metadata for all 10+ reproducible buggy fixtures."""
    return [
        {
            "id": f["id"],
            "name": f["name"],
            "category": f["category"],
            "file": f["file"],
            "description": f["description"]
        }
        for f in BENCHMARK_FIXTURES_META
    ]

@router.post("/run")
def execute_benchmark_suite():
    """Execute live evaluation run on the benchmark suite and return computed metrics."""
    results = run_benchmarks()
    return results
