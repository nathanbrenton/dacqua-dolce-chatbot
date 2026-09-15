# Authoritative Business Tool Boundary

Current pricing, inventory, installation availability, and other dynamic
business facts must not be invented by the language model.

The chatbot routes these requests through a BusinessDataProvider.

The default provider deliberately returns an unavailable result until a live
authoritative D'Acqua Dolce business-data source is connected.

The tool contract returns only customer-safe presentation text plus status and
source metadata. This prevents the chatbot from treating model memory as the
source of truth for dynamic business facts.

Pricing restrictions such as manufacturer advertising or MAP requirements
remain enforced separately by the server-controlled policy layer.

Planned production flow:

    User request
        |
        v
    Safety / compliance policy
        |
        v
    Business query router
        |
        +-- pricing --------> authoritative pricing service
        |
        +-- availability ---> authoritative operations service
        |
        +-- otherwise ------> language model

The production provider should ultimately communicate with the primary
D'Acqua Dolce backend/API rather than duplicate pricing or inventory data
inside the chatbot repository.

## Primary D'Acqua backend provider

The `dacqua_backend` provider retrieves authoritative customer-safe business
information from the primary D'Acqua HTTP API.

Configuration:

    DACQUA_BUSINESS_DATA_PROVIDER=dacqua_backend
    DACQUA_BACKEND_BASE_URL=http://127.0.0.1:8000

Pricing comes only from the public catalog response.

The chatbot honors `display_price`. If the backend withholds public pricing,
the chatbot does not inspect, reconstruct, estimate, or infer a hidden amount.

Availability comes from:

    GET /api/catalog/products/{slug}/availability

This customer-safe endpoint intentionally excludes raw quantity-on-hand and
reservation counts.

Installation-calendar availability is not currently modeled by an
authoritative D'Acqua scheduling interface, so the chatbot does not invent
installation slots.

The privileged operations catalog is not a chatbot data source.
