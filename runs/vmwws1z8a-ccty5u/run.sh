#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwws1z8a-ccty5u====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwws1z8a-ccty5u exit=${code}====="
exit "$code"
