"""Scores each evolved program: it must stay correct, and faster is
better. OpenEvolve calls evaluate() for every candidate it generates.
"""

import importlib.util
import time

N = 200_000
EXPECTED = 17_984  # number of primes below 200,000


def evaluate(program_path: str) -> dict:
    spec = importlib.util.spec_from_file_location("program", program_path)
    program = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(program)
        start = time.perf_counter()
        result = program.count_primes(N)
        elapsed = time.perf_counter() - start
    except Exception as exc:
        return {"combined_score": 0.0, "error": str(exc)}

    if result != EXPECTED:
        return {"combined_score": 0.0, "correctness": 0.0}

    # correct answers score by speed: 1.0 as elapsed approaches zero
    return {
        "combined_score": 1.0 / (1.0 + elapsed),
        "correctness": 1.0,
        "elapsed_seconds": elapsed,
    }
