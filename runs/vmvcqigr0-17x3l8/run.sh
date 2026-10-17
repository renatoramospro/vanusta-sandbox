#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcqigr0-17x3l8====="
(
  set -e
  python 'experiment_quic_tls.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcqigr0-17x3l8 exit=${code}====="
exit "$code"
