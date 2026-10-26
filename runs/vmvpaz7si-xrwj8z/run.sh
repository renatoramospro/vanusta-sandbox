#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvpaz7si-xrwj8z====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvpaz7si-xrwj8z exit=${code}====="
exit "$code"
