# Local Inference Baseline

## Environment

- Model: Qwen3-0.6B
- Runtime: PyTorch + Transformers
- Device: Apple MPS
- Python: 3.14
- Network dependency during inference: none
- Model loading with local_files_only=True: verified

## Smoke Test

Prompt:

    In one sentence, explain what reverse osmosis does.

Response:

    Reverse osmosis removes impurities and contaminants from water by forcing
    them through a semipermeable membrane.

## Timing

- Model load: 4.85 seconds
- Generation: 2.80 seconds
- Total: 7.66 seconds

This establishes the initial local-development baseline. It is not a
production performance benchmark.
