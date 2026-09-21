#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuai617q-5urvbe====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuai617q-5urvbe exit=${code}====="
exit "$code"
