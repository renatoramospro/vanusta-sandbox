#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubm1479-41uglb====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'jsonschema'
  python 'registry_demo.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubm1479-41uglb exit=${code}====="
exit "$code"
