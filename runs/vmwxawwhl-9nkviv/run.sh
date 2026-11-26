#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxawwhl-9nkviv====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxawwhl-9nkviv exit=${code}====="
exit "$code"
