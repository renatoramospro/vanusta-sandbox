#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugc8gtt-jaohql====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugc8gtt-jaohql exit=${code}====="
exit "$code"
