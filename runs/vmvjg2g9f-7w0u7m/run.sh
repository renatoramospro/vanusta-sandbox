#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvjg2g9f-7w0u7m====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvjg2g9f-7w0u7m exit=${code}====="
exit "$code"
