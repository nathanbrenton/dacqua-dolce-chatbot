# Retrieval Baseline

- Label: `pre-embedding-deterministic-lexical`
- Top-k: `3`
- Passed: `6/6`

| Case | Result | Retrieved |
| --- | --- | --- |
| retrieval-ro | PASS | water-reverse-osmosis |
| retrieval-carbon | PASS | water-carbon-filtration |
| retrieval-softener | PASS | water-softening, water-ultraviolet, water-reverse-osmosis |
| retrieval-conditioning | PASS | water-conditioning, water-softening, water-ultraviolet |
| retrieval-uv | PASS | water-ultraviolet, water-reverse-osmosis, water-softening |
| retrieval-claims | PASS | claims-boundary, water-reverse-osmosis, water-carbon-filtration |
