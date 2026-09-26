#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui8h7n2-ud4z0n====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui8h7n2-ud4z0n exit=${code}====="
exit "$code"
