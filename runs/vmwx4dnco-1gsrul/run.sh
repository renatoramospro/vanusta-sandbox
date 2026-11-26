#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx4dnco-1gsrul====="
(
  set -e
  python 'websocket_manager.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx4dnco-1gsrul exit=${code}====="
exit "$code"
