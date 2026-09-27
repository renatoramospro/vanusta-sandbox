#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk1mvre-vhd7sw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk1mvre-vhd7sw exit=${code}====="
exit "$code"
