#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvij5xxq-zvqsul====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvij5xxq-zvqsul exit=${code}====="
exit "$code"
