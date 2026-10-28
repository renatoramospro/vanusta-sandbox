#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvs62ibs-8osfps====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvs62ibs-8osfps exit=${code}====="
exit "$code"
