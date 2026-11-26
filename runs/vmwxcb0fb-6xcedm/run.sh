#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxcb0fb-6xcedm====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxcb0fb-6xcedm exit=${code}====="
exit "$code"
