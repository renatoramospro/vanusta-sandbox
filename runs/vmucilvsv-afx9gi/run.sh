#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucilvsv-afx9gi====="
(
  set -e
  python 'ai_readiness_model.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucilvsv-afx9gi exit=${code}====="
exit "$code"
