#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuasg7cj-9qa42l====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuasg7cj-9qa42l exit=${code}====="
exit "$code"
