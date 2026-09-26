#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhpeg0y-n6f8wv====="
(
  set -e
  python 'scheduler.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhpeg0y-n6f8wv exit=${code}====="
exit "$code"
