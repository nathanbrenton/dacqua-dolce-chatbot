# D'Acqua Dolce Chatbot

Standalone AI assistant service for D'Acqua Dolce.

The chatbot is developed independently from the primary D'Acqua Dolce web
application so its inference model, retrieval system, business tools, and API
can evolve without coupling the website to a particular AI provider.

## Architecture

Planned request path:

    D'Acqua Dolce website
            |
            v
    D'Acqua application/backend
            |
            v
    D'Acqua chatbot API
            |
            +-- inference provider
            +-- retrieval / knowledge
            +-- business tools
            +-- policy layer

The inference layer is intentionally provider-independent. Local Transformers,
MLX, hosted models, or OpenAI-compatible providers may be substituted without
changing the higher-level chatbot interface.

## Current Baseline

Local inference has been validated on:

- Apple M4 Max
- macOS
- Python 3.14
- PyTorch 2.12.1
- Transformers 5.8.1
- Apple Metal Performance Shaders (MPS)
- Qwen3-0.6B

The model and Python wheel archives are deliberately stored outside this Git
repository.

D'Acqua-specific offline assets:

    ~/Desktop/dacqua-dolce_build-assets/

General reusable offline assets:

    ~/Desktop/offline-assets/

## Offline Inference

Qwen3-0.6B has successfully loaded and generated a response using only local
assets with Hugging Face and Transformers offline modes enabled.

Baseline smoke test:

- model load: 4.85 seconds
- generation: 2.80 seconds
- total: 7.66 seconds
- device: Apple MPS

Test prompt:

    In one sentence, explain what reverse osmosis does.

Model response:

    Reverse osmosis removes impurities and contaminants from water by forcing
    them through a semipermeable membrane.

These measurements are an initial development baseline, not production
performance targets.

## Repository Policy

Do not commit:

- model weights
- virtual environments
- API keys or secrets
- private business data
- authoritative product pricing
- proprietary customer information
- local offline dependency archives

Dynamic business facts such as pricing, inventory, product availability, and
policy-restricted information should come from authoritative runtime data or
tools rather than being embedded into model weights.

## Development Direction

Near-term milestones:

1. inference-provider abstraction
2. Transformers/Qwen provider
3. FastAPI health and chat endpoints
4. automated tests
5. evaluation baseline
6. retrieval-augmented generation
7. business-data tools and policy enforcement
8. model/provider evaluation and replacement as appropriate

Fine-tuning is intentionally deferred until baseline model, retrieval, tool,
and evaluation results show that training is justified.

## License

MIT
