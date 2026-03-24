# python-polarion (v3)

Typed Python SDK for Polarion with a strict, service-oriented API.

## Requirements

- Python 3.9+

## Install

```bash
pip install polarion-api
```

## Quickstart

```python
from polarion import PolarionClient

with PolarionClient(url="https://polarion.example.com/polarion", username="user", token="token") as client:
    # API namespaces
    projects = client.projects
    workitems = client.workitems
    documents = client.documents
    plans = client.plans
    testruns = client.testruns
    users = client.users
```

## API shape (v3)

- `PolarionClient`
  - `projects`, `workitems`, `documents`, `plans`, `testruns`, `users`
- Typed models in `polarion.v3.types.*`
- Strict error hierarchy in `polarion.v3.errors`
- Parser layer in `polarion.v3.parser`
- Transport abstraction in `polarion.v3.transport`

## Current implementation status

This release provides a compileable v3 skeleton with explicit contracts:

- typed models
- service interfaces/signatures
- parser/transport scaffolding

Service method implementations are intentionally staged and will follow in subsequent PRs.

## Public entrypoint

```python
from polarion import PolarionClient
```

## License

MIT
