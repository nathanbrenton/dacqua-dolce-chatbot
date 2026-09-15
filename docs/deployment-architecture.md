# D'Acqua Dolce Chatbot Deployment Architecture

## P0 production decision

The D'Acqua Dolce web/business application and chatbot may use the same
PostgreSQL 17 service on the initial production server, but they must use
separate databases and separate database roles.

Planned logical layout:

    PostgreSQL 17 service
        |
        +-- dacqua_dolce
        |      role: dacqua_dolce_app
        |
        +-- dacqua_chatbot
               role: dacqua_chatbot_app

The chatbot must not receive credentials for, or make direct SQL queries
against, the `dacqua_dolce` business database.

## Business data trust boundary

Authoritative business information remains owned by the primary D'Acqua
backend.

Examples include:

- product records
- prices
- manufacturer/MAP presentation policy
- inventory
- customer records
- carts and orders
- quotes
- operational state

The chatbot accesses customer-safe business facts through the D'Acqua HTTP API.

Current flow:

    customer
       |
       v
    chatbot API
       |
       +-- deterministic policy
       |
       +-- business-data router
       |       |
       |       v
       |    D'Acqua backend HTTP API
       |       |
       |       v
       |    dacqua_dolce database
       |
       +-- language-model inference

The chatbot must never reconstruct a price that the primary backend has
withheld. The backend's pricing presentation decision is authoritative.

## Chatbot database

A separate `dacqua_chatbot` database is planned when persistence becomes
necessary.

Potential chatbot-owned data includes:

- retrieval/RAG document metadata
- chunk metadata
- embeddings or vector indexes
- evaluation metadata
- non-sensitive conversation/session state if persistence is approved
- retrieval caches

It must not become a second source of truth for product pricing, inventory,
customers, orders, or manufacturer policy.

No chatbot database is required yet for the current stateless P0 inference
and business-tool integration.

## Model storage

Language-model weights do not belong in PostgreSQL.

Model files remain filesystem/model-runtime assets and are loaded by the
inference provider independently of PostgreSQL.

## Future scaling

The initial deployment may keep both logical databases on one PostgreSQL
service.

If retrieval/vector workload later warrants separation, `dacqua_chatbot`
may move to another PostgreSQL service without changing the business-data
HTTP trust boundary.
