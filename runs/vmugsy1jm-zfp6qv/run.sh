#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugsy1jm-zfp6qv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugsy1jm-zfp6qv exit=${code}====="
exit "$code"
