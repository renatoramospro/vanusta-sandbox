#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9fxzoh-i7tz01====="
(
  set -e
  npm install --no-audit --no-fund --ignore-scripts --loglevel=error
  npm test
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9fxzoh-i7tz01 exit=${code}====="
exit "$code"
