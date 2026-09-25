#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmug8kpeb-fsuw3v====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmug8kpeb-fsuw3v exit=${code}====="
exit "$code"
