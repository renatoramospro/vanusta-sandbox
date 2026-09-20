#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9yy77f-8eskhk====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'numpy' 'pandas' 'scikit-learn'
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9yy77f-8eskhk exit=${code}====="
exit "$code"
