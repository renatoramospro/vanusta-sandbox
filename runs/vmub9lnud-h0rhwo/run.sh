#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub9lnud-h0rhwo====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub9lnud-h0rhwo exit=${code}====="
exit "$code"
