#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucie958-hfra4u====="
(
  set -e
  python 'ai_readiness_model.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucie958-hfra4u exit=${code}====="
exit "$code"
