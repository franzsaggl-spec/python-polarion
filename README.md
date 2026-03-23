# Python-polarion
[![Documentation Status](https://readthedocs.org/projects/python-polarion/badge/?version=latest)](https://python-polarion.readthedocs.io/en/latest/?badge=latest)
[![Downloads](https://pepy.tech/badge/polarion)](https://pepy.tech/project/polarion)


This package allows the user to access many Polarion items like workitems, test run, plans and documents.

# Maintainers needed!

Hi All, I need some extra hands to keep this going. Please leave a comment here if you're interested [here](https://github.com/jesper-raemaekers/python-polarion/discussions/148)

# Feature overview

This package can, among others, read, modify and create:
- Workitems
- Test runs from templates
- Plans
- Documents

Work with attachments in workitems and test runs. 
Work with custom field in workitems and documents.

# Installation

```
pip install polarion
```

# Getting started

Creating the Polarion client and getting workitems, test runs or plans:

```python
from polarion import polarion
client = polarion.Polarion('http://example.com/polarion', 'user', 'password')
project = client.getProject('Python')
workitem = project.getWorkitem('PYTH-510')
run = project.getTestRun('SWQ-0001')
plan = project.getPlan('00002')
```

Modifying workitems:

```python
workitem.setDescription('Some description..')
workitem.addComment('test comment', 'sent from Python')
workitem.addHyperlink('google.com', workitem.HyperlinkRoles.EXTERNAL_REF)
```

Or test run results:
```python
run = project.getTestRun('SWQ-0001')
run.records[0].setResult(record.Record.ResultType.PASSED, ' Comment with test result')
```

Adding workitems to a plan:
```python
plan.addToPlan(workitem)
plan.removeFromPlan(workitem)
```


More examples to be found in the quick start section of the documentation.
[Go to the documentation](https://python-polarion.readthedocs.io/)

# Usage in CLI Tools and AI Assistants

When using python-polarion in CLI tools or AI assistants like Claude Code, follow these context-efficient patterns to avoid overwhelming output buffers and context windows:

**✅ Recommended patterns:**
```python
# Count first, then decide whether to fetch
count = project.countWorkitems("status:open AND type:bug")
print(f"Found {count} open bugs")  # Just a number, not full objects
if count < 50:
    items = project.searchWorkitemFullItem("status:open AND type:bug", limit=50)

# Use lightweight searches for IDs/minimal fields only
workitem_refs = project.searchWorkitem("status:open", field_list=['id', 'title', 'status'])

# Get clean summaries for CLI output
wi = project.getWorkitem("PROJ-123")
print(wi.to_dict())  # {'id': 'PROJ-123', 'title': '...', 'type': 'bug', 'status': 'open'}

# Specify limits explicitly to control result size
recent_bugs = project.searchWorkitemFullItem("type:bug", order="created", limit=10)
```

**❌ Patterns to avoid:**
```python
# Don't fetch unlimited results (can return thousands of items!)
all_items = project.searchWorkitemFullItem("", limit=-1)

# Don't fetch full object graphs when you just need URIs
doc = project.getDocument("space/doc")
all_workitems = doc.getWorkitems()  # Use getWorkitemUris() instead

# Don't ignore the default limit and accidentally get only 100 when you need more
# Be explicit: limit=200 if you need 200, or limit=-1 if you truly need all
```

**Why this matters:**
CLI tools and AI assistants have limited output buffers. Fetching 1000 workitems with 50+ fields each can:
- Crash CLI tools with too much output
- Consume AI context windows (Claude Code shows all tool outputs in conversation)
- Make debugging difficult (too much noise in logs)
- Cause timeouts and poor performance

**Context-efficient methods:**
- `project.countWorkitems(query)` - Get count without fetching objects
- `project.countPlans(query)` - Get plan count
- `project.countTestRuns(query)` - Get test run count
- `workitem.to_dict(fields)` - Get clean dictionary representation
- `plan.to_dict()`, `testrun.to_dict()` - Summaries for other objects

**Default limits:**
Starting from version 2.0, search methods default to `limit=100` instead of unlimited. This prevents accidental large fetches. To get all results, explicitly pass `limit=-1`.

# How does it work?

This project uses the SOAP API of Polarion. This API exposes most of the user interactions you can do with Polarion like creating or editing workitems, plans and test runs.
The API is divided in seven different services which you can find from your Polarion instance at the url http://domain.com/polarion/ws/services.
Each of the services provides a WSDL file detailing the available functions. (Also available form you local instance at http://domain.com/polarion/ws/services/TrackerWebService?wsdl)
For this project the TrackerWebService, PlanningWebService and TestManagementWebService are the most used ones.

In general the project attempts for the objects (like workitems) to behave like Python objects which you can modify and are saved in the background. 
Where the API provide operation to preform an action that API call is used, and the object is reloaded from polarion to reflect the changes locally.

The API does not allow access to the project administration.

# Dependencies 

The package uses zeep, lxml, texttable, and requests.

It is tested for Python version 3.9 through 3.13.
Python 3.8 support has been dropped in 1.4.0.

# Known issues or missing features
- No way of knowing the test run possible statuses.
- Deleting work items used in documents does not remove the reference from the document.

