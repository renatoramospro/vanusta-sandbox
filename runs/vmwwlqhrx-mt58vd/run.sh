#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwlqhrx-mt58vd====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'packaging'
  python 'dependency_resolver.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwlqhrx-mt58vd exit=${code}====="
exit "$code"
