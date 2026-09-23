#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmueqzh6w-vh79rn====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmueqzh6w-vh79rn exit=${code}====="
exit "$code"
