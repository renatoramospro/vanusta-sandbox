#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcm4e8g-ji8kst====="
(
  set -e
  python 'forward_chaining.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcm4e8g-ji8kst exit=${code}====="
exit "$code"
