#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9wcq51-g3ez2k====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9wcq51-g3ez2k exit=${code}====="
exit "$code"
