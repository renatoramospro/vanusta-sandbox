#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhxz2xd-4t5pod====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhxz2xd-4t5pod exit=${code}====="
exit "$code"
