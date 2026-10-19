#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvf5f8kb-9e6bzd====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvf5f8kb-9e6bzd exit=${code}====="
exit "$code"
