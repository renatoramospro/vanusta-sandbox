#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuak49kf-mg78ck====="
(
  set -e
  python 'persistence_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuak49kf-mg78ck exit=${code}====="
exit "$code"
