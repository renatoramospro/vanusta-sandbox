#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuip7001-2k44u0====="
(
  set -e
  node 'tracer.js'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuip7001-2k44u0 exit=${code}====="
exit "$code"
