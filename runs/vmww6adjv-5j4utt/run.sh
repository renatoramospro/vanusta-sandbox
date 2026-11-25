#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww6adjv-5j4utt====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww6adjv-5j4utt exit=${code}====="
exit "$code"
