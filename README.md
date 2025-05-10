# Ansible Password Quality Module

This repository contains Ansible modules for managing password quality requirements on Linux systems through the `/etc/security/pwquality.conf` file.

## Overview

The `pwquality` module allows you to configure password quality requirements enforced by the pam_pwquality PAM module. It provides an idempotent way to manage all password quality parameters from your Ansible playbooks.

## Requirements

- Ansible 2.9 or later (compatible with both Ansible 2.12+ and older versions)
- Linux system with pam_pwquality installed
- Root/sudo access (to modify system configuration files)

## Included Modules

1. **pwquality.py**: Main module for managing `/etc/security/pwquality.conf` parameters
2. **my_test.py**: Test module to verify pwquality functionality

## Installation

1. Clone the repository:
   ```
   git clone <repository_url>
   cd ansible/pwquality
   ```

2. Use the modules in your playbooks by setting the library path:
   ```
   ansible-playbook -i inventory playbook.yml -e "ansible_library=./library"
   ```

   Or set the `ANSIBLE_LIBRARY` environment variable:
   ```
   ANSIBLE_LIBRARY=/path/to/ansible/pwquality/library ansible-playbook playbook.yml
   ```

## Ansible Version Compatibility

These modules are designed to work with multiple versions of Ansible:

- **Ansible 2.12+**: Uses the `run_module()` function pattern
- **Older Ansible versions**: Uses the traditional `main()` function pattern
- **Direct execution**: Can be run directly from the command line for testing

All versions use the same core functionality with different entry points to ensure compatibility.

## Usage Examples

### Basic Usage

```yaml
- name: Set minimum password length to 12
  pwquality:
    minlen: 12
  become: yes
```

### Configure Complex Password Requirements

```yaml
- name: Set complex password requirements
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
    backup: true
  become: yes
```

### Testing with Included Playbooks

The repository includes test playbooks:

```bash
# Test basic functionality
ANSIBLE_LIBRARY=./library ansible-playbook test_playbook.yml -v

# Test pwquality module (requires sudo)
ANSIBLE_LIBRARY=./library ansible-playbook pwquality_test.yaml -v --ask-become-pass
```

## Module Parameters

The `pwquality` module supports the following parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| difok | int | Number of characters in the new password that must not be present in the old password |
| minlen | int | Minimum acceptable size for the new password |
| dcredit | int | Credit/requirement for digits in the password (negative values enforce minimum count) |
| ucredit | int | Credit/requirement for uppercase characters |
| lcredit | int | Credit/requirement for lowercase characters |
| ocredit | int | Credit/requirement for other (special) characters |
| minclass | int | Minimum number of character classes required |
| maxrepeat | int | Maximum number of same consecutive characters |
| maxclassrepeat | int | Maximum number of consecutive same-class characters |
| maxsequence | int | Maximum length of monotonic character sequences |
| gecoscheck | int | Check GECOS field for password words |
| dictcheck | bool | Check password against dictionary words |
| usercheck | bool | Check password against username |
| badwords | list | Words to check for in passwords |
| dictpath | str | Path to the dictionary file |
| usersubstr | int | Length of username substrings to check |
| enforcing | int | Whether the checks should be enforced |
| retry | int | Number of retries allowed |
| enforce_for_root | bool | Whether to enforce checks for root user |
| local_users_only | bool | Whether to only enforce for local users |
| backup | bool | Whether to create a backup of the file before modification |

## Direct Command Line Usage

Both modules can be used directly on the command line for testing:

```bash
# Show current pwquality configuration
python library/pwquality.py --show

# Set minlen to 12
sudo python library/pwquality.py --minlen 12 --backup

# Test password file functionality
python library/my_test.py check
```

## License

GNU General Public License v3.0 or later

## Author

Your Name (@yourGitHubHandle)