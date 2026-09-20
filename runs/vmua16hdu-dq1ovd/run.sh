#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua16hdu-dq1ovd====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'numpy' 'scikit-learn'
  python 'federated_leak_detection.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua16hdu-dq1ovd exit=${code}====="
exit "$code"
