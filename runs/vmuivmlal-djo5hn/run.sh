#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuivmlal-djo5hn====="
(
  set -e
  python 'event_sourcing_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuivmlal-djo5hn exit=${code}====="
exit "$code"
