#!/bin/bash
cd "$(dirname "$0")"
python fetch.py $* 2>/dev/null || python3 fetch.py $*
