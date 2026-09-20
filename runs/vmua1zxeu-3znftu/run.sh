#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua1zxeu-3znftu====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'numpy' 'pandas' 'scikit-learn'
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua1zxeu-3znftu exit=${code}====="
exit "$code"
