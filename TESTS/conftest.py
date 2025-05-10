#!/usr/bin/env python
# Pytest configuration file for pwquality module tests

import os
import sys
import pytest
from unittest.mock import MagicMock

# Add the parent directory to the path so we can import from library
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now we can import the library modules using full package path
# import library.pwquality as ansible_pwquality


@pytest.fixture
def mock_ansible_module():
    """Fixture to provide a mock AnsibleModule instance."""
    mock_module = MagicMock()
    mock_module.params = {}
    mock_module.check_mode = False
    mock_module.exit_json.side_effect = SystemExit(0)
    mock_module.fail_json.side_effect = SystemExit(1)
    return mock_module


@pytest.fixture
def mock_pwquality_config():
    """Fixture to provide a mock for the pwquality.conf file content."""
    return """# Configuration for systemwide password quality limits
# Defaults:
#
# Number of characters in the new password that must not be present in the
# old password.
# difok = 1
#
# Minimum acceptable size for the new password (plus one if
# credits are not disabled which is the default). (See pam_cracklib manual.)
minlen = 9
#
# The maximum credit for having digits in the new password. If less than 0
# it is the minimum number of digits in the new password.
dcredit = 0
#
# The maximum credit for having uppercase characters in the new password.
# If less than 0 it is the minimum number of uppercase characters in the
# new password.
ucredit = 0
#
# The maximum credit for having lowercase characters in the new password.
# If less than 0 it is the minimum number of lowercase characters in the
# new password.
lcredit = 0
"""