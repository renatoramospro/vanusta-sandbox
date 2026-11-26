#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx50xkk-u7mysp====="
(
  set -e
  python 'websocket_manager.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx50xkk-u7mysp exit=${code}====="
exit "$code"
