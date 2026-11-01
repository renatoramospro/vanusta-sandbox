#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvy1q26w-8npyj6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvy1q26w-8npyj6 exit=${code}====="
exit "$code"
