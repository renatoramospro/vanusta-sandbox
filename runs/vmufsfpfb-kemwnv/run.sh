#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufsfpfb-kemwnv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufsfpfb-kemwnv exit=${code}====="
exit "$code"
