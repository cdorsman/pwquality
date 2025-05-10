#!/usr/bin/env python
# Unit tests for my_test.py module

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the library directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import library.my_test as ansible_my_test


class TestMyTestModule(unittest.TestCase):
    """Unit tests for the my_test module"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock for AnsibleModule
        self.mock_ansible_module = MagicMock()
        self.mock_ansible_module.params = {"action": "test"}
        self.mock_ansible_module.exit_json.side_effect = SystemExit(0)
        self.mock_ansible_module.fail_json.side_effect = SystemExit(1)

    @patch("library.my_test.AnsibleModule", autospec=True)
    def test_run_module_test_action(self, mock_ansible_module_class):
        """Test the module with 'test' action"""
        # Set up the mock
        mock_instance = mock_ansible_module_class.return_value
        mock_instance.params = {"action": "test"}
        
        # Call the module
        try:
            ansible_my_test.run_module()
        except SystemExit:
            pass
        
        # Verify the exit_json was called with correct args
        mock_instance.exit_json.assert_called_once()
        args = mock_instance.exit_json.call_args[1]
        self.assertFalse(args["changed"])
        self.assertEqual(args["message"], "This is a test module for pwquality")
    
    @patch("library.my_test.AnsibleModule", autospec=True)
    @patch("library.my_test.os.path.exists")
    @patch("builtins.open")
    def test_run_module_check_action_file_exists(self, mock_open, mock_exists, mock_ansible_module_class):
        """Test the module with 'check' action when the config file exists"""
        # Set up the mocks
        mock_instance = mock_ansible_module_class.return_value
        mock_instance.params = {"action": "check"}
        mock_exists.return_value = True
        
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "test content"
        mock_open.return_value = mock_file
        
        # Call the module
        try:
            ansible_my_test.run_module()
        except SystemExit:
            pass
        
        # Verify the exit_json was called with correct args
        mock_instance.exit_json.assert_called_once()
        args = mock_instance.exit_json.call_args[1]
        self.assertFalse(args["changed"])
        self.assertTrue(args["exists"])
        self.assertEqual(args["content_length"], 12)  # Length of "test content"
    
    @patch("library.my_test.AnsibleModule", autospec=True)
    @patch("library.my_test.os.path.exists")
    def test_run_module_check_action_file_not_exists(self, mock_exists, mock_ansible_module_class):
        """Test the module with 'check' action when the config file doesn't exist"""
        # Set up the mocks
        mock_instance = mock_ansible_module_class.return_value
        mock_instance.params = {"action": "check"}
        mock_exists.return_value = False
        
        # Call the module
        try:
            ansible_my_test.run_module()
        except SystemExit:
            pass
        
        # Verify the exit_json was called with correct args
        mock_instance.exit_json.assert_called_once()
        args = mock_instance.exit_json.call_args[1]
        self.assertFalse(args["changed"])
        self.assertFalse(args["exists"])


if __name__ == "__main__":
    unittest.main()