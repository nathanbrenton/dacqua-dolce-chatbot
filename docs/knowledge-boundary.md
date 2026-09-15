# D'Acqua Dolce Chatbot Knowledge Boundary

## Purpose

Retrieval-augmented generation is for curated, relatively stable knowledge.

It is not a substitute for authoritative runtime business systems.

## Eligible retrieval knowledge

Examples:

- general water-treatment education
- approved product-family explanations
- approved installation and maintenance documentation
- approved product specifications
- approved manufacturer documentation
- approved certifications and product claims
- stable brand terminology
- stable customer-facing policies
- customer-safe FAQs

Every retrievable document must have:

- a stable document ID
- a source
- a scope
- curated text
- enough provenance to decide whether it may be used in a customer answer

## Runtime-only authoritative information

The following must remain outside the general RAG corpus when current state
matters:

- current prices
- MAP or price-display decisions
- current inventory
- current installation availability
- current scheduling
- customer records
- carts
- orders
- payment state
- quote state
- account state

These facts come from the primary D'Acqua backend through controlled business
tools.

## Restricted knowledge

The retrieval corpus must not contain:

- secrets
- passwords
- API keys
- database credentials
- private customer information
- internal-only operational data unless an explicit internal chatbot surface
  is later designed
- hidden prices or data intentionally withheld by the authoritative backend

## Claims

A general educational document is not sufficient authority for a specific
health, contaminant-reduction, certification, or performance claim.

Such claims require approved source material.

## Initial retrieval implementation

The first retriever is deterministic and lexical.

It deliberately uses no embedding model and no vector database.

This baseline gives us measurable retrieval behavior before adding semantic
retrieval infrastructure.
