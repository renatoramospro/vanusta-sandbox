#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcq6wja-72dt5y====="
(
  set -e
  python 'experiment_quic_tls.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcq6wja-72dt5y exit=${code}====="
exit "$code"
