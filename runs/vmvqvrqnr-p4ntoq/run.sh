#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvqvrqnr-p4ntoq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvqvrqnr-p4ntoq exit=${code}====="
exit "$code"
