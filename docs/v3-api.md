# v3 API Reference (Draft)

## Client

```python
from polarion import PolarionClient

client = PolarionClient(url=..., username=..., token=...)
```

Namespaces:
- `client.projects`
- `client.users`
- `client.workitems`
- `client.documents`
- `client.plans`
- `client.testruns`

## ProjectsService
- `get(project_id)`
- `list(query=None, offset=0, limit=100)`
- `users(project_id, offset=0, limit=200)`

## UsersService
- `get(user_id)`
- `search(query=None, offset=0, limit=100)`

## WorkitemsService
- `get(project_id, workitem_id)`
- `get_by_uri(uri)`
- `create(project_id, payload)`
- `update(project_id, workitem_id, payload)`
- `delete(project_id, workitem_id)`
- `search(project_id, query=None, sort="Created", fields=None, offset=0, limit=100)`
- `available_actions(...)`, `available_statuses(...)`, `perform_action(...)`
- link/hyperlink/attachment/test-step helpers

## DocumentsService
- `get(project_id, uri=...|location=...)`
- `create(project_id, payload)`
- `delete(project_id, uri)`
- `save(document)`
- `list_spaces(project_id)`
- `list_locations(project_id)`
- `list_in_space(project_id, space, offset=0, limit=100)`
- `workitems(...)`, `top_level_workitem(...)`, `children(...)`, `parent(...)`
- `export_pdf(...)`, `reuse(...)`

## PlansService
- `get(project_id, plan_id)`
- `create(project_id, payload)`
- `update(plan)`
- `delete(project_id, plan_id)`
- `search(project_id, query=None, sort="Created", offset=0, limit=100)`
- `workitems(project_id, plan_id, offset=0, limit=200)`
- `add_workitem(...)`, `remove_workitem(...)`

## TestRunsService
- `get(project_id, test_run_id)`
- `get_by_uri(uri)`
- `search(project_id, query=None, sort="Created", offset=0, limit=100)`
- `create(project_id, payload)`
- `update(testrun)`
- `records(test_run_uri, offset=0, limit=500)`
- `add_test_case(test_run_uri, workitem_uri)`
- attachments methods

## Errors
- `PolarionError`
- `AuthError`
- `TransportError`
- `ValidationError`
- `NotFoundError`
- `ParsingError`
- `ConflictError`

## Notes
- Pagination returns `Page[T]` with `items`, `total`, `offset`, `limit`, `has_more`.
- Live integration tests are opt-in (`--run-integration`).
