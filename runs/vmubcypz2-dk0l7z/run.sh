#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubcypz2-dk0l7z====="
(
  set -e
  python 'combat_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubcypz2-dk0l7z exit=${code}====="
exit "$code"
