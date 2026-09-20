#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua2z74d-zffwhu====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua2z74d-zffwhu exit=${code}====="
exit "$code"
