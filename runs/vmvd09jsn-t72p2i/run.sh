#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvd09jsn-t72p2i====="
(
  set -e
  python 'oidc_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvd09jsn-t72p2i exit=${code}====="
exit "$code"
