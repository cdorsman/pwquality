#!/usr/bin/env python
# Unit tests for pwquality.py module

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add the library directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import library.pwquality as ansible_pwquality
from library.pwquality import PwqualityConfig


class TestPwqualityModule(unittest.TestCase):
    """Unit tests for the pwquality module"""

    def setUp(self):
        """Set up test fixtures"""
        self.module = MagicMock()
        self.module.params = {
            "minlen": 12,
            "dcredit": -1,
            "backup": True
        }
        self.module.check_mode = False
        self.module.exit_json.side_effect = SystemExit(0)
        self.module.fail_json.side_effect = SystemExit(1)

    @patch("library.pwquality.AnsibleModule", autospec=True)
    def test_module_init(self, mock_ansible_module_class):
        """Test module initialization"""
        # Set up the mock
        mock_instance = mock_ansible_module_class.return_value
        mock_instance.params = {
            "minlen": 12,
            "dcredit": -1,
            "backup": True
        }
        mock_instance.check_mode = False

        # Mock PwqualityConfig to prevent actual file operations
        with patch.object(ansible_pwquality, 'PwqualityConfig') as mock_config:
            mock_config_instance = mock_config.return_value
            mock_config_instance.ensure_state.return_value = True
            mock_config_instance.changes = {"minlen": "12", "dcredit": "-1"}
            mock_config_instance.backup_file = "/etc/security/pwquality.conf.backup"
            
            # Call the module
            try:
                ansible_pwquality.run_module()
            except SystemExit:
                pass
            
            # Verify PwqualityConfig was initialized correctly
            mock_config.assert_called_once_with(mock_instance)
            mock_config_instance.ensure_state.assert_called_once()
            
            # Verify exit_json was called with correct args
            mock_instance.exit_json.assert_called_once()
            args = mock_instance.exit_json.call_args[1]
            self.assertTrue(args["changed"])
            self.assertEqual(args["changes"], {"minlen": "12", "dcredit": "-1"})
            self.assertEqual(args["backup_file"], "/etc/security/pwquality.conf.backup")


class TestPwqualityConfig(unittest.TestCase):
    """Unit tests for the PwqualityConfig class"""

    def setUp(self):
        """Set up test fixtures"""
        self.module = MagicMock()
        self.module.params = {
            "minlen": 12,
            "dcredit": -1,
            "backup": True
        }
        self.module.check_mode = False
        self.module.exit_json.side_effect = SystemExit(0)
        self.module.fail_json.side_effect = SystemExit(1)

    @patch("os.path.exists")
    def test_check_pwquality_config_exists(self, mock_exists):
        """Test check_pwquality_config when file exists"""
        mock_exists.return_value = True
        config = PwqualityConfig(self.module)
        # No exception should be raised
        self.assertEqual(config.config_file, "/etc/security/pwquality.conf")

    @patch("os.path.exists")
    def test_check_pwquality_config_not_exists(self, mock_exists):
        """Test check_pwquality_config when file doesn't exist"""
        mock_exists.return_value = False
        with self.assertRaises(SystemExit):
            PwqualityConfig(self.module)
        self.module.fail_json.assert_called_once()

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="minlen = 9\ndcredit = 0\n")
    def test_read_config(self, mock_file, mock_exists):
        """Test read_config method"""
        mock_exists.return_value = True
        config = PwqualityConfig(self.module)
        result = config.read_config()
        self.assertEqual(result, {"minlen": "9", "dcredit": "0"})

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="minlen = 9\ndcredit = 0\n")
    def test_ensure_state_with_changes(self, mock_file, mock_exists):
        """Test ensure_state when changes are needed"""
        mock_exists.return_value = True
        
        # Create a config with changes needed
        config = PwqualityConfig(self.module)
        
        # Mock write_config and create_backup to avoid actual file operations
        config.write_config = MagicMock()
        config.create_backup = MagicMock()
        
        # Call ensure_state
        result = config.ensure_state()
        
        # Check results
        self.assertTrue(result)  # Should return True for changed
        self.assertTrue(config.changed)
        self.assertEqual(config.changes, {"minlen": "12", "dcredit": "-1"})
        config.create_backup.assert_called_once()
        config.write_config.assert_called_once()

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="minlen = 12\ndcredit = -1\n")
    def test_ensure_state_no_changes(self, mock_file, mock_exists):
        """Test ensure_state when no changes are needed"""
        mock_exists.return_value = True
        
        # Create a config with no changes needed (values already match)
        config = PwqualityConfig(self.module)
        
        # Mock write_config and create_backup to avoid actual file operations
        config.write_config = MagicMock()
        config.create_backup = MagicMock()
        
        # Call ensure_state
        result = config.ensure_state()
        
        # Check results
        self.assertFalse(result)  # Should return False for no changes
        self.assertFalse(config.changed)
        self.assertEqual(config.changes, {})
        config.create_backup.assert_not_called()
        config.write_config.assert_not_called()


if __name__ == "__main__":
    unittest.main()