# polarion-api

[![PyPI version](https://badge.fury.io/py/polarion-api.svg)](https://pypi.org/project/polarion-api/)
[![Python Support](https://img.shields.io/pypi/pyversions/polarion-api.svg)](https://pypi.org/project/polarion-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/saggl/python-polarion/actions/workflows/ci.yml/badge.svg)](https://github.com/saggl/python-polarion/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/python-polarion/badge/?version=latest)](https://python-polarion.readthedocs.io/en/latest/)

**A Python client for the Polarion Application Lifecycle Management (ALM) platform.**

`polarion-api` provides a Pythonic interface to Polarion's SOAP API, enabling you to automate workitem management, test execution tracking, planning, and document operations. Perfect for test automation frameworks, CI/CD pipelines, and development tooling.

## Features

- **Workitems**: Create, read, update, and query workitems with full field access
- **Test Management**: Execute test runs, update test records, work with test templates
- **Planning**: Manage plans, add/remove workitems, track progress
- **Documents**: Access and manipulate Polarion documents and their structure
- **Attachments**: Upload and download attachments for workitems and test runs
- **Custom Fields**: Full support for custom field definitions and values
- **CLI/AI Friendly**: Optimized methods for use in CLI tools and AI assistants

## 📦 Installation

```bash
pip install polarion-api
```

> **Note:** The package is installed as `polarion-api` on PyPI but imported as `polarion`:
> ```python
> from polarion import polarion
> ```
> This naming maintains compatibility with existing code while providing a distinct PyPI package name.

## 🚀 Quick Start

### Connecting to Polarion

```python
from polarion import polarion

client = polarion.Polarion('http://example.com/polarion', 'user', 'password')
project = client.getProject('PROJECT_ID')
```

### Working with Workitems

```python
# Get a workitem
workitem = project.getWorkitem('PROJ-123')

# Modify workitem
workitem.setDescription('Updated description')
workitem.addComment('test comment', 'sent from Python')
workitem.addHyperlink('google.com', workitem.HyperlinkRoles.EXTERNAL_REF)
```

### Managing Test Runs

```python
# Get test run and update results
run = project.getTestRun('SWQ-0001')
run.records[0].setResult(record.Record.ResultType.PASSED, 'Test passed successfully')
```

### Working with Plans

```python
# Get plan and manage workitems
plan = project.getPlan('plan-id')
plan.addToPlan(workitem)
plan.removeFromPlan(workitem)
```

For complete examples, see the [Documentation](https://python-polarion.readthedocs.io/).

## 💡 Usage in CLI Tools and AI Assistants

When using `polarion-api` in CLI tools or AI assistants like Claude Code, follow these context-efficient patterns to avoid overwhelming output buffers and context windows:

### ✅ Recommended Patterns

```python
# Use lightweight searches for IDs/minimal fields only
workitem_refs = project.searchWorkitem("status:open", field_list=['id', 'title', 'status'])

# Get clean summaries for CLI output
wi = project.getWorkitem("PROJ-123")
print(wi.to_dict())  # {'id': 'PROJ-123', 'title': '...', 'type': 'bug', 'status': 'open'}

# Specify limits explicitly to control result size
recent_bugs = project.searchWorkitemFullItem("type:bug", order="created", limit=10)
```

### ❌ Patterns to Avoid

```python
# Don't fetch unlimited results (can return thousands of items!)
all_items = project.searchWorkitemFullItem("", limit=-1)

# Don't fetch full object graphs when you just need URIs
doc = project.getDocument("space/doc")
all_workitems = doc.getWorkitems()  # Use getWorkitemUris() instead

# Don't ignore the default limit and accidentally get only 100 when you need more
# Be explicit: limit=200 if you need 200, or limit=-1 if you truly need all
```

### Why This Matters

CLI tools and AI assistants have limited output buffers. Fetching 1000 workitems with 50+ fields each can:
- Crash CLI tools with excessive output
- Consume AI context windows (Claude Code shows all tool outputs)
- Make debugging difficult (too much noise in logs)
- Cause timeouts and performance issues

### Context-Efficient Methods

- `workitem.to_dict(fields)` - Clean dictionary representation
- `plan.to_dict()`, `testrun.to_dict()`, `document.to_dict()` - Object summaries
- `project.searchWorkitem(query, field_list=['id', 'title'])` - Lightweight searches
- `document.getWorkitemUris()` - URIs instead of full objects

### Default Limits

Starting from version 2.0, search methods default to `limit=100` instead of unlimited. This prevents accidental large fetches. To get all results, explicitly pass `limit=-1`.

## How It Works

This package uses Polarion's SOAP API, which exposes most user interactions available in the Polarion web interface. The API is divided into seven different services accessible from your Polarion instance at:

```
http://your-polarion-domain.com/polarion/ws/services
```

Each service provides a WSDL file detailing available functions:
- **TrackerWebService** - Workitem operations
- **PlanningWebService** - Plan management
- **TestManagementWebService** - Test run execution

The package wraps these services in Pythonic objects that behave like native Python classes. When you modify objects (e.g., `workitem.setDescription()`), the changes are saved to Polarion automatically and the object is reloaded to reflect the current state.

**Note:** The API does not provide access to project administration functions.

## Requirements

- **Python**: 3.9, 3.10, 3.11, 3.12, 3.13
- **Dependencies**: zeep, lxml, texttable, requests

Python 3.8 support was dropped in version 1.4.0.

## 📚 Documentation

Full documentation is available at [python-polarion.readthedocs.io](https://python-polarion.readthedocs.io/).

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

Issues and pull requests are welcome! Please check the [issue tracker](https://github.com/saggl/python-polarion/issues) for existing issues or to report bugs and feature requests.

## Known Issues

- No method to determine available test run statuses programmatically
- Deleting workitems referenced in documents does not automatically remove the document reference

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

This project is a maintained fork of the original [python-polarion](https://github.com/jesper-raemaekers/python-polarion) by Jesper Raemaekers.

This fork includes:
- Comprehensive CI/CD pipeline with GitHub Actions
- Type hints and modern Python best practices
- Expanded test coverage with pytest
- Quality improvements, bug fixes, and code simplification
- Active maintenance and updates

The project remains MIT licensed and welcomes contributions.
