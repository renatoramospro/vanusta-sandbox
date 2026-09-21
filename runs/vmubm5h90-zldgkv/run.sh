#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubm5h90-zldgkv====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'jsonschema'
  python 'registry_demo.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubm5h90-zldgkv exit=${code}====="
exit "$code"
