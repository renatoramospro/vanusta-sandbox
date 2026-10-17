#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcd842y-he19cw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcd842y-he19cw exit=${code}====="
exit "$code"
