#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9xofns-4mx43d====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9xofns-4mx43d exit=${code}====="
exit "$code"
