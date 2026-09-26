#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiqdg8v-bmwuv8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiqdg8v-bmwuv8 exit=${code}====="
exit "$code"
