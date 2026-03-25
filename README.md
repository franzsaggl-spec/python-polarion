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

v3 now includes:

- typed models
- service interfaces/signatures
- parser layer and SOAP transport wiring
- baseline service implementations for projects, users, workitems, documents, plans, and test runs

## Live integration test harness (opt-in)

A live smoke test harness is available under `tests/integration/`.

It is disabled by default and only runs when explicitly enabled:

```bash
pytest tests/integration --run-integration -v
```

Required env vars:

- `POLARION_URL`
- `POLARION_USERNAME`
- `POLARION_PASSWORD` **or** `POLARION_TOKEN`
- `POLARION_PROJECT_ID`

Optional:

- `POLARION_VERIFY_SSL` (`true|false`, default `true`)
- `POLARION_TIMEOUT` (seconds, default `30`)
- `POLARION_WORKITEM_ID` (enables direct workitem get smoke)
- `POLARION_DOCUMENT_URI` (enables direct document get smoke)
- `POLARION_PLAN_ID` (enables direct plan get smoke)
- `POLARION_TESTRUN_ID` (enables direct test run get smoke)

## Public entrypoint

```python
from polarion import PolarionClient
```

## API reference

- See `docs/v3-api.md` for a service-by-service v3 API contract.

## License

MIT
