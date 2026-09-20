#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9ymynn-bcvjil====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'numpy' 'pandas' 'scikit-learn'
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9ymynn-bcvjil exit=${code}====="
exit "$code"
