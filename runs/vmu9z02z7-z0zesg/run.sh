#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9z02z7-z0zesg====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'numpy' 'pandas' 'scikit-learn'
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9z02z7-z0zesg exit=${code}====="
exit "$code"
