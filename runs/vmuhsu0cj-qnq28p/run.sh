#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhsu0cj-qnq28p====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhsu0cj-qnq28p exit=${code}====="
exit "$code"
