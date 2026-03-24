# polarion-api

A Python client for the Polarion Application Lifecycle Management (ALM) platform.

`polarion-api` provides a Pythonic interface to Polarion's web services, enabling you to automate workitem management, test execution tracking, planning, and document operations. Designed for test automation frameworks, CI/CD pipelines, and development tooling.

## Features

- **Work items** -- Create, read, update, search, delete, with full field access
- **Test management** -- Test runs, test records, set results, test step attachments
- **Planning** -- Manage plans, add/remove work items, track dates and progress
- **Documents** -- Access, create, export PDF, navigate structure, reuse across projects
- **Attachments** -- Upload and download attachments on work items, test runs, and test records
- **Custom fields** -- Get and set custom field values on any supported object
- **Context managers** -- `with Polarion(...) as client:` and `with workitem.batch():`
- **JUnit XML import** -- Import test results from JUnit XML files into Polarion test runs

## Requirements

- **Python**: 3.10+
- **Dependencies**: requests, lxml, texttable

## Installation

```bash
pip install polarion-api
```

The package is installed as `polarion-api` from PyPI but imported as `polarion`:

```python
from polarion import Polarion
```

## Quick Start

### Connecting to Polarion

Use the client as a context manager. Authenticate with either a password or a personal access token.

```python
from polarion import Polarion

# Password authentication
with Polarion("https://polarion.example.com/polarion", "user", password="pw") as client:
    project = client.get_project("MyProject")
    wi = project.get_workitem("REQ-123")
    print(wi.title)

# Token authentication
with Polarion("https://polarion.example.com/polarion", "user", token="personal-access-token") as client:
    project = client.get_project("MyProject")
```

Additional options:

```python
with Polarion(
    "https://polarion.example.com/polarion",
    "user",
    password="pw",
    verify_certificate=True,       # or path to CA bundle
    proxy="proxy-host:8080",       # optional HTTP proxy
    svn_repo_url="https://...",    # custom SVN repo URL
    static_service_list=False,     # True to skip WSDL discovery
) as client:
    ...
```

### Working with Work Items

```python
project = client.get_project("MyProject")

# Get a work item
wi = project.get_workitem("REQ-123")
print(wi.title, wi.status, wi.type)

# Modify and save explicitly
wi.title = "Updated title"
wi.save()

# Batch multiple changes into a single save
with wi.batch() as w:
    w.title = "New title"
    w.description = {"content": "<p>New description</p>", "type": "text/html", "contentLossy": False}
# save() is called once on exit

# Create a new work item
new_wi = project.create_workitem("requirement", fields={"title": "My new requirement"})

# Search (lightweight -- returns dicts with requested fields)
results = project.search_workitems("type:bug AND status:open", field_list=["id", "title", "status"])

# Search (full objects)
bugs = project.search_workitems_full("type:bug", order="Created", limit=50)

# Delete
wi.delete()
```

### Descriptions and Custom Fields

```python
# Read description content
desc_html = wi.get_description()

# Set a custom field
wi.set_custom_field("myCustomField", "some value")
value = wi.get_custom_field("myCustomField")
```

### Links, Hyperlinks, and Comments

```python
# Link two work items
wi.add_linked_item(other_wi, "relates_to")
wi.remove_linked_item(other_wi, "relates_to")
linked = wi.get_linked_items_with_roles()  # list of (role, Workitem) tuples

# Hyperlinks
wi.add_hyperlink("https://example.com", wi.HyperlinkRoles.EXTERNAL_REF)

# Comments
wi.add_comment("Comment title", "Comment body as HTML")
```

### Attachments

```python
# Work item attachments
wi.add_attachment("/path/to/file.pdf", "My attachment")
data = wi.get_attachment("attachment-id")
wi.save_attachment_as_file("attachment-id", "/path/to/output.pdf")
wi.delete_attachment("attachment-id")
```

### Test Steps

```python
# Get test steps
steps = wi.get_test_steps()       # list of dicts
header = wi.get_test_step_header() # column names

# Add / update / remove
wi.add_test_step("Step action", "Expected result")
wi.update_test_step(0, "Updated action", "Updated result")
wi.remove_test_step(0)
```

### Workflow Actions

```python
actions = wi.get_available_actions()
wi.perform_action("reopen")

statuses = wi.get_available_statuses()
```

### Test Runs and Records

```python
# Get a test run
run = project.get_test_run("SWQ-0001")

# Search test runs
runs = project.search_test_runs("status:open", limit=20)

# Create a test run from a template
new_run = project.create_test_run("RUN-001", "Nightly Tests", "template-id")

# Access records
for record in run.records:
    print(record.testcase_id, record.get_result())

# Set result on a record
from polarion import Record
run.records[0].set_result(Record.ResultType.PASSED, "Test passed successfully")

# Set test step result
run.records[0].set_test_step_result(0, Record.ResultType.PASSED, "Step OK")

# Add a test case to a run
run.add_test_case(wi)

# Test run attachments
run.add_attachment("/path/to/log.txt", "Test log")
```

### Documents

```python
# Get a document
doc = project.get_document("_default/MyDocument")

# Create a document
doc = project.create_document(
    location="_default",
    name="NewDoc",
    title="New Document",
    allowed_workitem_types=["requirement"],
    structure_link_role="parent",
)

# Export to PDF
pdf_bytes = doc.export_to_pdf()
with open("output.pdf", "wb") as f:
    f.write(pdf_bytes)

# Get work items in a document
uris = doc.get_workitem_uris()         # lightweight URI list
workitems = doc.get_workitems()        # full Workitem objects (slower)
top = doc.get_top_level_workitem()

# Navigate document structure
children = doc.get_children(workitem)
parent = doc.get_parent(workitem)

# Add a heading
doc.add_heading("Section Title", parent_workitem=top)

# Reuse a document in another project
reused = doc.reuse(
    target_project_id="OtherProject",
    target_location="_default",
    target_name="ReusedDoc",
    target_title="Reused Document",
)

# Document spaces and locations
spaces = project.get_document_spaces()
locations = project.get_document_locations()
docs = project.get_documents_in_space("_default")
```

### Plans

```python
# Get a plan
plan = project.get_plan("release-1.0")

# Create a plan
plan = project.create_plan(
    name="Release 2.0",
    plan_id="release-2.0",
    template="release",
    parent=parent_plan,  # optional
)

# Search plans
plans = project.search_plans_full("name:Release*", limit=10)

# Add / remove work items
plan.add_workitem(wi)
plan.remove_workitem(wi)

# Get work items in a plan
items = plan.get_workitems()

# Dates
from datetime import date
plan.set_start_date(date(2026, 1, 1))
plan.set_due_date(date(2026, 6, 30))

# Navigate plan hierarchy
children = plan.get_children()
parent = plan.get_parent()
```

### Users

```python
# Get all project users
users = project.get_users()

# Find a user by ID or name
user = project.find_user("jsmith")
```

### Enumerations

```python
# Get enum options for a work item type
statuses = project.get_enum("requirement-status")
resolutions = project.get_enum("bug-resolution")

# From a work item instance
wi.get_status_enum()
wi.get_resolution_enum()
wi.get_severity_enum()
```

### JUnit XML Import

Import JUnit XML test results into Polarion test runs.

```python
from polarion.xml import Config, Importer

config = Config(
    xml_file="results.xml",
    url="https://polarion.example.com/polarion",
    project_id="MyProject",
    username="user",
    password="pw",
    testrun_title="Nightly CI Run",
    testrun_type="xUnit Test Manual Upload",
    skip_missing_testcase=False,
)

test_run = Importer.from_xml(config)

# Or load config from JSON
config = Config.from_json("config.json")
test_run = Importer.from_xml(config)
```

## CLI and AI Assistant Usage

When using `polarion-api` in CLI tools or AI assistants, follow these patterns to avoid large output and context overflow:

```python
# Use lightweight searches -- return only the fields you need
results = project.search_workitems("status:open", field_list=["id", "title", "status"])

# Use to_dict() for clean summaries
wi = project.get_workitem("REQ-123")
print(wi.to_dict())  # {'id': 'REQ-123', 'title': '...', 'type': 'bug', 'status': 'open'}

# Specify limits explicitly
recent = project.search_workitems_full("type:bug", order="Created", limit=10)

# Use URIs instead of full objects for documents
uris = doc.get_workitem_uris()  # much faster than doc.get_workitems()
```

Search methods default to `limit=100`. Pass `limit=-1` to retrieve all results.

## How It Works

This package communicates with Polarion's SOAP web services at:

```
https://your-polarion-server.com/polarion/ws/services
```

The main services used are:

- **TrackerWebService** -- Work item and document operations
- **PlanningWebService** -- Plan management
- **TestManagementWebService** -- Test run and record operations
- **ProjectWebService** -- Project and user operations

All SOAP communication is handled internally using `requests` and `lxml` for XML construction and parsing. Objects returned from the API behave like regular Python objects with attribute access.

The API does not provide access to project administration functions.

## Development

### Setup

```bash
git clone https://github.com/saggl/python-polarion.git
cd python-polarion
pip install -e ".[test]"
```

### Testing

```bash
pytest
```

### Linting

```bash
ruff check .
```

### Contributing

Issues and pull requests are welcome. See the [issue tracker](https://github.com/saggl/python-polarion/issues).

## Known Issues

- No method to determine available test run statuses programmatically
- Deleting work items referenced in documents does not automatically remove the document reference

## Migration from v1

Version 2.0.0 is a major rewrite. The following breaking changes apply.

### Python version

Python 3.10 or later is required. Support for 3.8 and 3.9 has been dropped.

### Dependencies

The `zeep` dependency has been removed. SOAP communication is now handled with `requests` and `lxml`. No changes are needed in your code unless you were accessing zeep internals.

### Method naming

All public methods have been renamed from camelCase to snake_case:

| v1 | v2 |
|---|---|
| `client.getProject()` | `client.get_project()` |
| `project.getWorkitem()` | `project.get_workitem()` |
| `project.createWorkitem()` | `project.create_workitem()` |
| `project.searchWorkitemFullItem()` | `project.search_workitems_full()` |
| `project.getTestRun()` | `project.get_test_run()` |
| `project.getPlan()` | `project.get_plan()` |
| `project.getDocument()` | `project.get_document()` |
| `workitem.setDescription()` | Direct attribute assignment + `wi.save()` |
| `workitem.setCustomField()` | `workitem.set_custom_field()` |
| `workitem.addLinkedItem()` | `workitem.add_linked_item()` |
| `workitem.addComment()` | `workitem.add_comment()` |
| `workitem.addHyperlink()` | `workitem.add_hyperlink()` |
| `record.setResult()` | `record.set_result()` |

### Client usage

The `Polarion` client now supports context managers. Import path changed:

```python
# v1
from polarion import polarion
client = polarion.Polarion('http://example.com/polarion', 'user', 'password')

# v2
from polarion import Polarion
with Polarion("https://example.com/polarion", "user", password="pw") as client:
    ...
```

### Explicit save

Setter methods no longer save automatically. Modify attributes directly and call `save()`:

```python
# v1
workitem.setDescription("New description")  # saved immediately

# v2
wi.description = {"content": "New description", "type": "text/html", "contentLossy": False}
wi.save()  # explicit save required
```

### Batch save

`PostponeSaveMixin` has been replaced by the `batch()` context manager:

```python
# v1
workitem.postponeSave = True
workitem.setTitle("New")
workitem.setDescription("Desc")
workitem.save()

# v2
with wi.batch() as w:
    w.title = "New"
    w.description = {"content": "Desc", "type": "text/html", "contentLossy": False}
# save() called once on exit
```

### Config class

The JUnit XML importer `Config` is now a `@dataclass`. Use keyword arguments instead of a dict:

```python
# v1
config = {"xml_file": "results.xml", "url": "...", ...}

# v2
from polarion.xml import Config
config = Config(xml_file="results.xml", url="...", project_id="MyProject", username="user", password="pw")
```

### Factory functions

`createFromUri` has been renamed to `create_from_uri`, and `addCreator` has been renamed to `register_creator`. These are internal functions and unlikely to affect most users.

### Search defaults

Search methods now default to `limit=100` instead of unlimited. Pass `limit=-1` explicitly if you need all results.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Credits

This project is a maintained fork of the original [python-polarion](https://github.com/jesper-raemaekers/python-polarion) by Jesper Raemaekers. It includes a rewritten SOAP transport layer, full snake_case API, type hints, expanded test coverage, and active maintenance.
