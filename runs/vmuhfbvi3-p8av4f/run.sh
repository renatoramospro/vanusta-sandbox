#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhfbvi3-p8av4f====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhfbvi3-p8av4f exit=${code}====="
exit "$code"
