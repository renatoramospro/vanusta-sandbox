#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuje5zvx-dnbpte====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuje5zvx-dnbpte exit=${code}====="
exit "$code"
