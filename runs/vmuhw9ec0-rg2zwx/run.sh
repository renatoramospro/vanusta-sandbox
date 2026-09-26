#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhw9ec0-rg2zwx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhw9ec0-rg2zwx exit=${code}====="
exit "$code"
