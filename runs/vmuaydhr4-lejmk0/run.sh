#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaydhr4-lejmk0====="
(
  set -e
  python 'tutorial_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaydhr4-lejmk0 exit=${code}====="
exit "$code"
