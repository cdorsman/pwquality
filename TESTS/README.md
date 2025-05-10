# Testing the pwquality Module

This directory contains test scripts and playbooks for the pwquality Ansible module.

## Quick Start

To execute all tests, make the test script executable and run it:

```bash
chmod +x test_direct.sh
./test_direct.sh
```

## Test Files

1. **test_playbook.yml** - Tests the basic functionality of the `my_test` module
2. **pwquality_test.yaml** - Tests the main `pwquality` module (requires sudo privileges)
3. **test_direct.sh** - Tests direct execution of the modules
4. **inventory** - Local inventory file for Ansible testing

## Running Ansible Tests

Run the test playbooks with:

```bash
# Test basic functionality (my_test module)
ansible-playbook -i inventory test_playbook.yml -v

# Test pwquality module (requires sudo)
ansible-playbook -i inventory pwquality_test.yaml -v --ask-become-pass
```

You can also specify the library path if needed:

```bash
ANSIBLE_LIBRARY=../library ansible-playbook -i inventory test_playbook.yml -v
```

## Compatibility Testing

The modules are designed to work with:
- Ansible 2.12 (current focus)
- Older versions of Ansible (2.9+)
- Newer versions of Ansible (2.13+)

## Manual Testing

You can manually test the modules with:

```bash
# Test my_test module
python ../library/my_test.py test
python ../library/my_test.py check

# Test pwquality module
python ../library/pwquality.py --show
sudo python ../library/pwquality.py --minlen 12 --backup
```