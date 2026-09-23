#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue7tkn1-5hu2p9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue7tkn1-5hu2p9 exit=${code}====="
exit "$code"
