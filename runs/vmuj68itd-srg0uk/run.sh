#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj68itd-srg0uk====="
(
  set -e
  python 'skiplist_concorrente.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj68itd-srg0uk exit=${code}====="
exit "$code"
