#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9o4grc-2xr39m====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9o4grc-2xr39m exit=${code}====="
exit "$code"
