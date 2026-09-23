#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue6brba-h10jfw====="
(
  set -e
  node 'generate_report.js'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue6brba-h10jfw exit=${code}====="
exit "$code"
