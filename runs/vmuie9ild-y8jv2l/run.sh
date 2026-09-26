#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuie9ild-y8jv2l====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuie9ild-y8jv2l exit=${code}====="
exit "$code"
