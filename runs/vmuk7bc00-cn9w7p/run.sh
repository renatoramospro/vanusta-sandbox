#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk7bc00-cn9w7p====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk7bc00-cn9w7p exit=${code}====="
exit "$code"
