#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuir8cf8-oizj3m====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuir8cf8-oizj3m exit=${code}====="
exit "$code"
