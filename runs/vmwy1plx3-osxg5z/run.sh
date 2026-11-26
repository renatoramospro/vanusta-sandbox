#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwy1plx3-osxg5z====="
(
  set -e
  python 'protocol_module.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwy1plx3-osxg5z exit=${code}====="
exit "$code"
