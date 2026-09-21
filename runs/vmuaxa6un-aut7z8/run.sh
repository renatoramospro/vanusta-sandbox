#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaxa6un-aut7z8====="
(
  set -e
  python 'localization_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaxa6un-aut7z8 exit=${code}====="
exit "$code"
