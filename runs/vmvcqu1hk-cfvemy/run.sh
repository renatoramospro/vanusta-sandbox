#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcqu1hk-cfvemy====="
(
  set -e
  python 'experiment_quic_tls.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcqu1hk-cfvemy exit=${code}====="
exit "$code"
