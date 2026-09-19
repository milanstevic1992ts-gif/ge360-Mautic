# GE360 integration contracts

These contracts define the payloads exchanged between Prospex, Mautic, SuiteCRM, n8n and Jarvis.

The first contract is `lead.schema.json`.

Rules:

1. `source` identifies where the record originated.
2. `external_id` is the source-system identifier and should be used for idempotency.
3. Marketing consent is explicit. Missing consent must never be treated as consent.
4. Systems may add fields under `meta`, but should not silently rename canonical fields.
5. API tokens never belong in payloads; they travel in headers/environment configuration.
