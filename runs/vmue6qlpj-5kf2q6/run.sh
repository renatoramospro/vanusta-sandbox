#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue6qlpj-5kf2q6====="
(
  set -e
  node 'generate_report_secure.js'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue6qlpj-5kf2q6 exit=${code}====="
exit "$code"
