#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import json

from ansible.module_utils.basic import AnsibleModule

# Add Ansible compatibility metadata
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: pwquality

short_description: Manage password quality requirements on Linux

version_added: "1.0.0"

description:
  - This module modifies the password quality requirements in /etc/security/pwquality.conf.
  - Uses the pam_pwquality module configuration.

options:
    difok:
        description: Number of characters in the new password that must not be present in the old password.
        required: false
        type: int
    minlen:
        description:
            - Minimum acceptable size for the new password (plus one if credits are not disabled which is the default.
            - Cannot be set to lower value than 6. (default 9).
        required: false
        type: int
    dcredit:
        description: 
            - The maximum credit for having digits in the new password. 
            - If less than 0 it is the minimum number of digits in the new password.
        required: false
        type: int
    ucredit:
        description: 
            - The maximum credit for having uppercase characters in the new password. 
            - If less than 0 it is the minimum number of uppercase characters in the new password. 
        required: false
        type: int
    lcredit:
        description: 
            - The maximum credit for having lowercase characters in the new password.
            - If less than 0 it is the minimum number of lowercase characters in the new password. 
        required: false
        type: int
    ocredit:
        description: 
            - The maximum credit for having other characters in the new password. 
            - If less than 0 it is the minimum number of other characters in the new password. 
        required: false
        type: int
    minclass:
        description: Minimum number of character classes that must be present in the new password.
        required: false
        type: int
    maxrepeat:
        description: 
            - The maximum number of allowed same consecutive characters in the new password. 
            - The check is disabled if the value is 0.
        required: false
        type: int
    maxclassrepeat:
        description: Maximum number of allowed consecutive characters belonging to the same character class.
        required: false
        type: int
    maxsequence:
        description:
            - Maximum number of allowed consecutive characters in the new password.
            - The check is disabled if the value is 0.
        required: false
        type: int
    gecoscheck:
        description:
            - If nonzero, check whether the words longer than 3 characters from the GECOS field of the user's 
                passwd(5) entry are contained in the new password. 
            - The check is disabled if the value is 0.
        required: false
        type: int
    dictcheck:
        description: Check the password against a dictionary.
        required: false
        type: bool
    usercheck:
        description: Check the password against the username.
        required: false
        type: bool
    badwords:
        description: Check the password against a list of bad words.
        required: false
        type: list 
        elements: str
    dictpath:
        description: Path to the dictionary file.
        required: false
        type: str
    usersubstr:
        description: Check the password against the username substring.
        required: false
        type: int
    enforcing:
        description: Enforce the password policy.
        required: false
        type: int
    retry:
        description: Number of allowed retries.
        required: false
        type: int
    enforce_for_root:
        description: Enforce the password policy for the root user.
        required: false
        type: bool
    local_users_only:
        description: Enforce the password policy only for local users.
        required: false
        type: bool
    backup:
        description: Create a backup of the original file when modified
        required: false
        type: bool
        default: false

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Set minimum password length to 12
- name: Set minimum password length
  pwquality:
    minlen: 12

# Enforce complex password requirements
- name: Configure complex password requirements
  pwquality:
    minlen: 14
    dcredit: -1
    ucredit: -1
    lcredit: -1
    ocredit: -1
    minclass: 4
    maxrepeat: 2
    dictcheck: true
    usercheck: true

# Create a backup of the original file
- name: Set credit requirements with backup
  pwquality:
    dcredit: -2
    ucredit: -2
    backup: true
'''

RETURN = r'''
changes:
    description: Dictionary of parameters that were changed
    type: dict
    returned: changed
    sample: {"minlen": "12", "dcredit": "-1"}
backup_file:
    description: Path to the backup file if created
    type: str
    returned: when backup is true and file is changed
    sample: "/etc/security/pwquality.conf.2025-05-10@12:13:14~"
'''


def convert_bool(value):
    if value is True:
        return 1
    if value is False:
        return 0
    return value


def param_name_remap(name):
    """Convert module parameter names to pwquality.conf parameter names if needed"""
    # Some parameters might need different naming between module and config file
    remap = {
        'enforce_for_root': 'enforcing_for_root',
        'local_users_only': 'local_users_only'
    }
    return remap.get(name, name)


class PwqualityConfig:
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.config_file = '/etc/security/pwquality.conf'
        self.changed = False
        self.changes = {}
        self.backup_file = None
        self.check_pwquality_config()

    def check_pwquality_config(self):
        """Check if the pwquality.conf file exists"""
        if not os.path.exists(self.config_file):
            self.module.fail_json(msg=f'{self.config_file} does not exist')

    def create_backup(self):
        """Create a backup of the pwquality.conf file if requested"""
        if self.params['backup']:
            from datetime import datetime
            import shutil
            backup_time = datetime.now().strftime("%Y-%m-%d@%H:%M:%S~")
            backup_file = f"{self.config_file}.{backup_time}"
            try:
                shutil.copy2(self.config_file, backup_file)
                self.backup_file = backup_file
            except Exception as e:
                self.module.fail_json(msg=f"Cannot create backup file: {str(e)}")

    def read_config(self):
        """Read and parse the current pwquality.conf file"""
        current_config = {}
        
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        current_config[key.strip()] = value.strip()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to read config file: {str(e)}")

        return current_config

    def write_config(self, config):
        """Write the updated configuration back to pwquality.conf"""
        # Read the original file to preserve comments and structure
        try:
            with open(self.config_file, 'r') as f:
                lines = f.readlines()
                
            # Find existing settings and update them
            updated_lines = []
            params_found = set()
            
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped or line_stripped.startswith('#'):
                    updated_lines.append(line)
                    continue

                if '=' in line_stripped:
                    key, _ = line_stripped.split('=', 1)
                    key = key.strip()
                    if key in config:
                        updated_lines.append(f"{key} = {config[key]}\n")
                        params_found.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Add new parameters that weren't in the original file
            for key, value in config.items():
                if key not in params_found:
                    updated_lines.append(f"{key} = {value}\n")
                    
            # Write the updated content back to the file
            with open(self.config_file, 'w') as f:
                f.writelines(updated_lines)
                
        except Exception as e:
            self.module.fail_json(msg=f"Failed to write config file: {str(e)}")

    def ensure_state(self):
        """Update the pwquality configuration with the provided parameters"""
        # Read the current configuration
        current_config = self.read_config()
        
        # Track changes to make
        changes = {}
        
        # Process parameters to update
        for param_name, param_value in self.params.items():
            # Skip module control parameters
            if param_name in ['backup']:
                continue
                
            # Skip parameters with None value (not specified by user)
            if param_value is None:
                continue
                
            # Convert boolean values to integers
            if isinstance(param_value, bool):
                param_value = convert_bool(param_value)
                
            # Convert lists to comma-separated strings
            if isinstance(param_value, list):
                param_value = ','.join(param_value)
                
            # Get the correct parameter name for pwquality.conf
            config_param = param_name_remap(param_name)
            
            # Convert value to string for comparison and storage
            param_value_str = str(param_value)
            
            # Check if the parameter is already set correctly
            if config_param not in current_config or current_config[config_param] != param_value_str:
                changes[config_param] = param_value_str
        
        # If there are changes to make
        if changes:
            self.changed = True
            self.changes = changes
            
            # Create backup if requested
            if self.params['backup']:
                self.create_backup()
                
            # Update current config with changes
            current_config.update(changes)
            
            # Write the updated configuration
            self.write_config(current_config)

        return self.changed


def run_module():
    # This is the function Ansible 2.12+ uses
    module_args = dict(
        difok=dict(type='int', required=False),
        minlen=dict(type='int', required=False),
        dcredit=dict(type='int', required=False),
        ucredit=dict(type='int', required=False),
        lcredit=dict(type='int', required=False),
        ocredit=dict(type='int', required=False),
        minclass=dict(type='int', required=False),
        maxrepeat=dict(type='int', required=False),
        maxclassrepeat=dict(type='int', required=False),
        maxsequence=dict(type='int', required=False),
        gecoscheck=dict(type='int', required=False),
        dictcheck=dict(type='bool', required=False),
        usercheck=dict(type='bool', required=False),
        badwords=dict(type='list', elements='str', required=False),
        dictpath=dict(type='str', required=False),
        usersubstr=dict(type='int', required=False),
        enforcing=dict(type='int', required=False),
        retry=dict(type='int', required=False),
        enforce_for_root=dict(type='bool', required=False),
        local_users_only=dict(type='bool', required=False),
        backup=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Initialize the config object
    pwquality_config = PwqualityConfig(module)
    
    # Check mode: don't make any changes
    if module.check_mode:
        module.exit_json(changed=False)
    
    # Apply the configuration
    changed = pwquality_config.ensure_state()
    
    # Prepare the result
    result = {
        'changed': changed
    }
    
    # Add changes information if there were any
    if pwquality_config.changes:
        result['changes'] = pwquality_config.changes
        
    # Add backup information if a backup was created
    if pwquality_config.backup_file:
        result['backup_file'] = pwquality_config.backup_file
        
    module.exit_json(**result)


# For older versions of Ansible (pre-2.12)
def main():
    run_module()


# Direct execution for CLI-based testing
def direct_execution():
    """Handle direct command-line execution for testing"""
    import argparse
    from pprint import pprint
    
    # Create a class that mimics AnsibleModule for direct execution
    class MockModule:
        def __init__(self, params):
            self.params = params
            self.check_mode = False
            
        def fail_json(self, **kwargs):
            print(f"ERROR: {kwargs.get('msg', 'Unknown error')}")
            sys.exit(1)
            
        def exit_json(self, **kwargs):
            print("SUCCESS:")
            pprint(kwargs)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Manage pwquality.conf parameters')
    parser.add_argument('--difok', type=int, help='Number of characters in the new password that must not be present in the old password')
    parser.add_argument('--minlen', type=int, help='Minimum acceptable size for the new password')
    parser.add_argument('--dcredit', type=int, help='The maximum credit for having digits in the new password')
    parser.add_argument('--ucredit', type=int, help='The maximum credit for having uppercase characters in the new password')
    parser.add_argument('--lcredit', type=int, help='The maximum credit for having lowercase characters in the new password')
    parser.add_argument('--ocredit', type=int, help='The maximum credit for having special characters in the new password')
    parser.add_argument('--minclass', type=int, help='Minimum number of required character classes')
    parser.add_argument('--maxrepeat', type=int, help='Maximum number of allowed same consecutive characters in the new password')
    parser.add_argument('--backup', action='store_true', help='Create a backup of the configuration file')
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    
    args = parser.parse_args()
    
    # Convert namespace to dictionary, filtering out None values
    params = {k: v for k, v in vars(args).items() if v is not None and k != 'show'}
    
    # Show current configuration if requested
    if args.show:
        try:
            with open('/etc/security/pwquality.conf', 'r') as f:
                print("Current pwquality.conf content:")
                print(f.read())
            return
        except Exception as e:
            print(f"Error reading configuration: {str(e)}")
            return
    
    # Check if any parameters were provided
    if not params:
        parser.print_help()
        return
        
    # Create a mock module and run the config
    mock_module = MockModule(params)
    config = PwqualityConfig(mock_module)
    config.ensure_state()


if __name__ == '__main__':
    # Try to detect direct execution vs Ansible execution
    if len(sys.argv) > 1 or sys.stdin.isatty():
        # Running directly from command line
        direct_execution()
    else:
        # Running from Ansible - this works for all versions
        main()