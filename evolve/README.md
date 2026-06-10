# Evolve code with your local model

This folder is a ready-to-run [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve)
experiment wired to your Ollama server — an open-source take on
DeepMind's AlphaEvolve. Your local model mutates a program over many
generations; an evaluator keeps only versions that stay correct and
score better. No API keys, everything local.

## The example task

`initial_program.py` counts primes below 200,000 with a deliberately
naive algorithm. `evaluator.py` rejects anything incorrect and rewards
speed. Watch your model discover sieve-style algorithms on its own.

## Run it

```bash
source .venv/bin/activate
pip install openevolve

# make sure ollama serve is running, then:
openevolve-run evolve/initial_program.py evolve/evaluator.py \
    --config evolve/config.yaml --iterations 50
```

Progress and checkpoints land in `openevolve_output/` — the best program
so far is saved at each checkpoint.

## Expectations on a local 14B model

Each iteration is one or more LLM calls, so 50 iterations takes on the
order of an hour. Frontier-model results (GPU kernel speedups, etc.)
need thousands of iterations with stronger models — locally, treat this
as a way to optimize your own functions and learn how evolutionary
coding works, not to break records.

## Evolve your own code

1. Put your function in a copy of `initial_program.py` between the
   `EVOLVE-BLOCK-START` / `EVOLVE-BLOCK-END` markers.
2. Rewrite `evaluate()` in a copy of `evaluator.py` to score it —
   correctness gate first, then whatever metric you care about
   (speed, accuracy, memory, output quality).
3. Run the same command with your files. The better your evaluator,
   the better the evolution.
