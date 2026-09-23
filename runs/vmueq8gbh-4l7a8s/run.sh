#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmueq8gbh-4l7a8s====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmueq8gbh-4l7a8s exit=${code}====="
exit "$code"
