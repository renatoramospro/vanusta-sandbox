#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufzfqt7-f34dhx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufzfqt7-f34dhx exit=${code}====="
exit "$code"
