#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudqs0c7-i55bke====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudqs0c7-i55bke exit=${code}====="
exit "$code"
