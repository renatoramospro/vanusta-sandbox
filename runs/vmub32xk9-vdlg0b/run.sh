#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub32xk9-vdlg0b====="
(
  set -e
  python 'achievement_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub32xk9-vdlg0b exit=${code}====="
exit "$code"
