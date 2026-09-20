#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuac6rss-ad28j7====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuac6rss-ad28j7 exit=${code}====="
exit "$code"
