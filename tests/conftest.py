"""Root conftest: skip integration tests unless POLARION_LIVE is set."""

import os
import sys

# Skip integration tests unless POLARION_LIVE env var is set
collect_ignore_glob = []
if not os.environ.get('POLARION_LIVE'):
    collect_ignore_glob.extend([
        'test_polarion_*.py',
        'test_junit.py'
    ])
    # Also prevent import errors from keys.py by providing a dummy
    sys.modules['keys'] = type(sys)('keys')
    sys.modules['keys'].polarion_user = ''
    sys.modules['keys'].polarion_password = ''
    sys.modules['keys'].polarion_url = ''
    sys.modules['keys'].polarion_project_id = ''
