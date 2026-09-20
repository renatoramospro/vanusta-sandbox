#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua1l3n6-o4gcn1====="
(
  set -e
  npm install --no-audit --no-fund --ignore-scripts --loglevel=error
  npm test
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua1l3n6-o4gcn1 exit=${code}====="
exit "$code"
