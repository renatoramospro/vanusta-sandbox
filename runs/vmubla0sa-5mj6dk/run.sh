#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubla0sa-5mj6dk====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubla0sa-5mj6dk exit=${code}====="
exit "$code"
