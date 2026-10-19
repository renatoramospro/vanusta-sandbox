#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvft7q95-ckp755====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvft7q95-ckp755 exit=${code}====="
exit "$code"
