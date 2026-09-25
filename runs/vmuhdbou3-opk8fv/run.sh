#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhdbou3-opk8fv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhdbou3-opk8fv exit=${code}====="
exit "$code"
