#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiwp514-h739q7====="
(
  set -e
  python 'event_sourcing_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiwp514-h739q7 exit=${code}====="
exit "$code"
