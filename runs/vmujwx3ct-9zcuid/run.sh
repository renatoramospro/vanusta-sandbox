#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujwx3ct-9zcuid====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'numpy>=1.20.0'
  python 'vector_search.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujwx3ct-9zcuid exit=${code}====="
exit "$code"
