#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9sqtqz-kqak9b====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9sqtqz-kqak9b exit=${code}====="
exit "$code"
