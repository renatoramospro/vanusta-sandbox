#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmug6icva-ir0fuv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmug6icva-ir0fuv exit=${code}====="
exit "$code"
