#!/bin/bash
# Direct execution test script for pwquality module

echo "===== Testing my_test.py module ====="
python ../library/my_test.py test
echo ""
python ../library/my_test.py check
echo ""

echo "===== Testing pwquality.py module ====="
python ../library/pwquality.py --show
echo ""
echo "To test setting parameters, run with sudo:"
echo "sudo python ../library/pwquality.py --minlen 12 --backup"
echo ""