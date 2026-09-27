#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk6zrx9-nkqdil====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk6zrx9-nkqdil exit=${code}====="
exit "$code"
