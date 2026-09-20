#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua2bxbz-fcu86h====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'numpy' 'pandas' 'scikit-learn'
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua2bxbz-fcu86h exit=${code}====="
exit "$code"
