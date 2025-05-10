#!/usr/bin/env python
# Pytest-style tests for pwquality.py module

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

# Add the library directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "library")))
# Use a more explicit import with alias to avoid conflicts with system libraries
import library.pwquality as ansible_pwquality
from library.pwquality import PwqualityConfig, convert_bool, param_name_remap


# Test utility functions
@pytest.mark.parametrize("input_val,expected", [
    (True, 1),
    (False, 0),
    (5, 5),
    ("string", "string"),
    (None, None)
])
def test_convert_bool(input_val, expected):
    """Test the convert_bool function with various inputs"""
    assert convert_bool(input_val) == expected


@pytest.mark.parametrize("param_name,expected", [
    ("enforce_for_root", "enforcing_for_root"),
    ("local_users_only", "local_users_only"),
    ("minlen", "minlen"),  # No remapping
    ("dcredit", "dcredit")  # No remapping
])
def test_param_name_remap(param_name, expected):
    """Test the param_name_remap function"""
    assert param_name_remap(param_name) == expected


# Test PwqualityConfig class methods
def test_check_pwquality_config_exists(mock_ansible_module):
    """Test check_pwquality_config when file exists"""
    with patch("os.path.exists", return_value=True):
        config = PwqualityConfig(mock_ansible_module)
        assert config.config_file == "/etc/security/pwquality.conf"


def test_check_pwquality_config_not_exists(mock_ansible_module):
    """Test check_pwquality_config when file doesn't exist"""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(SystemExit):
            PwqualityConfig(mock_ansible_module)
        mock_ansible_module.fail_json.assert_called_once()


def test_read_config(mock_ansible_module, mock_pwquality_config):
    """Test read_config method with real-looking config file"""
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_pwquality_config)):
            config = PwqualityConfig(mock_ansible_module)
            result = config.read_config()
            assert result == {"minlen": "9", "dcredit": "0", "ucredit": "0", "lcredit": "0"}


# Test parameter handling scenarios
@pytest.mark.parametrize("current_config,module_params,expected_changes,should_change", [
    # No changes needed
    ({"minlen": "12", "dcredit": "-1"}, {"minlen": 12, "dcredit": -1, "backup": False}, {}, False),
    
    # Changes needed
    ({"minlen": "9", "dcredit": "0"}, {"minlen": 12, "dcredit": -1, "backup": True}, {"minlen": "12", "dcredit": "-1"}, True),
    
    # Mixed changes (one param changes, one stays the same)
    ({"minlen": "12", "dcredit": "0"}, {"minlen": 12, "dcredit": -1, "backup": False}, {"dcredit": "-1"}, True),
    
    # Boolean conversion
    ({"dictcheck": "1"}, {"dictcheck": True, "backup": False}, {}, False),
    ({"dictcheck": "0"}, {"dictcheck": True, "backup": False}, {"dictcheck": "1"}, True),
    
    # New parameter (not in current config)
    ({"minlen": "9"}, {"maxrepeat": 3, "backup": True}, {"maxrepeat": "3"}, True)
])
def test_ensure_state_scenarios(mock_ansible_module, current_config, module_params, expected_changes, should_change):
    """Test different scenarios for ensure_state"""
    mock_ansible_module.params = module_params
    
    with patch("os.path.exists", return_value=True):
        config = PwqualityConfig(mock_ansible_module)
        
        # Mock methods to avoid actual file operations
        config.read_config = MagicMock(return_value=current_config)
        config.write_config = MagicMock()
        config.create_backup = MagicMock()
        
        # Call ensure_state
        result = config.ensure_state()
        
        # Check results
        assert result == should_change
        assert config.changed == should_change
        assert config.changes == expected_changes
        
        # Check if backup was created and write_config was called
        if should_change:
            if mock_ansible_module.params.get("backup"):
                config.create_backup.assert_called_once()
            config.write_config.assert_called_once()
        else:
            config.create_backup.assert_not_called()
            config.write_config.assert_not_called()


# Test module integration with mocked dependencies
def test_run_module_integration():
    """Test the overall module integration"""
    with patch("library.pwquality.AnsibleModule") as mock_ansible_module_class:
        # Set up the mock instance
        mock_instance = mock_ansible_module_class.return_value
        mock_instance.params = {
            "minlen": 12,
            "dcredit": -1,
            "backup": True
        }
        mock_instance.check_mode = False
        
        # Make sure exit_json raises SystemExit - this is the key fix
        mock_instance.exit_json.side_effect = SystemExit(0)
        
        # Mock PwqualityConfig
        with patch.object(ansible_pwquality, "PwqualityConfig") as mock_config_class:
            mock_config = mock_config_class.return_value
            mock_config.ensure_state.return_value = True
            mock_config.changes = {"minlen": "12", "dcredit": "-1"}
            mock_config.backup_file = "/etc/security/pwquality.conf.backup"
            
            # Call the module, capturing SystemExit
            with pytest.raises(SystemExit):
                ansible_pwquality.run_module()
            
            # Verify interactions
            mock_config_class.assert_called_once_with(mock_instance)
            mock_instance.exit_json.assert_called_once()
            
            # Check arguments passed to exit_json
            call_args = mock_instance.exit_json.call_args[1]
            assert call_args["changed"] is True
            assert call_args["changes"] == {"minlen": "12", "dcredit": "-1"}
            assert call_args["backup_file"] == "/etc/security/pwquality.conf.backup"