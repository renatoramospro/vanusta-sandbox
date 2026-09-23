#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue4wph7-4vrifa====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue4wph7-4vrifa exit=${code}====="
exit "$code"
