#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhlbxs4-6ekgpv====="
(
  set -e
  python 'dns_iterative_server.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhlbxs4-6ekgpv exit=${code}====="
exit "$code"
