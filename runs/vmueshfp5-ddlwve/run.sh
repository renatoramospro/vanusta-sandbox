#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmueshfp5-ddlwve====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmueshfp5-ddlwve exit=${code}====="
exit "$code"
