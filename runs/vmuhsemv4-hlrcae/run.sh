#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhsemv4-hlrcae====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhsemv4-hlrcae exit=${code}====="
exit "$code"
