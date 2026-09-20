#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9ii31f-j2gb9i====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9ii31f-j2gb9i exit=${code}====="
exit "$code"
