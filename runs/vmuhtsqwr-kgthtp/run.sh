#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhtsqwr-kgthtp====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhtsqwr-kgthtp exit=${code}====="
exit "$code"
