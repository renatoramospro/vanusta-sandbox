#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuihderl-4g9pgz====="
(
  set -e
  python 'di_container.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuihderl-4g9pgz exit=${code}====="
exit "$code"
