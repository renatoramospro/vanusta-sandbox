#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudvdao9-oaabo8====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'PyYAML==6.0.1'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudvdao9-oaabo8 exit=${code}====="
exit "$code"
