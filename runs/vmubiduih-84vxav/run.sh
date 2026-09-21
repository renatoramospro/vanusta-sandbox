#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubiduih-84vxav====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubiduih-84vxav exit=${code}====="
exit "$code"
