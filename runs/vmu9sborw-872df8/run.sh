#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9sborw-872df8====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9sborw-872df8 exit=${code}====="
exit "$code"
