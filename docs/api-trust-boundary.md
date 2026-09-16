# Chatbot HTTP API Trust Boundary

## Server-controlled system prompt

The public `/v1/chat` endpoint accepts conversation messages only with these
roles:

- `user`
- `assistant`

A caller cannot submit a `system` role.

The chatbot service prepends its own server-controlled system prompt before
policy evaluation, business-data routing, retrieval, and inference.

This prevents the public client from assigning itself system-level authority.

## Internal orchestration

Internal code and evaluation tools may still construct `ChatMessage` values
with a `system` role.

That distinction is intentional:

    public HTTP client
        -> user / assistant messages only

    trusted server code
        -> may construct system messages

## Request ordering

The effective request path remains:

    server system prompt
        |
        v
    user conversation
        |
        v
    deterministic policy
        |
        v
    authoritative business tools
        |
        v
    curated retrieval
        |
        v
    inference provider

Retrieved documents are also server-selected reference data. They do not grant
the caller system-prompt control.
