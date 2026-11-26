#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxa5iur-rydodv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxa5iur-rydodv exit=${code}====="
exit "$code"
