#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhewfx2-0cj7wv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhewfx2-0cj7wv exit=${code}====="
exit "$code"
