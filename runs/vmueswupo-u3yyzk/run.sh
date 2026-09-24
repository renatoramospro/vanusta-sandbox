#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmueswupo-u3yyzk====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmueswupo-u3yyzk exit=${code}====="
exit "$code"
