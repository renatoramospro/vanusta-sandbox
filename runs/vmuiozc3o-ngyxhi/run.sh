#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiozc3o-ngyxhi====="
(
  set -e
  node 'tracer.js'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiozc3o-ngyxhi exit=${code}====="
exit "$code"
