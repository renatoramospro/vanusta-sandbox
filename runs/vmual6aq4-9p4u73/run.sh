#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmual6aq4-9p4u73====="
(
  set -e
  python 'animation_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmual6aq4-9p4u73 exit=${code}====="
exit "$code"
