#!/bin/bash
cd "$(dirname "$0")"
OUTPUT=$(./run.sh dump | tail -n +2)
[[ ! -d backup ]] && mkdir backup
zip -r ./backup/results-$USER-$(date '+%Y%m%d%H%M%S').zip . -x "*.zip" -x "backup/*" -x "bin/*" -x "*.exe" -x "hbd" -x "*.txt" -x "*.bat" -x "*.sh" -x "*.php" -x "*.py" -x "*.pyc" -x "*__pycache__/*" -x "*.gitignore" -x ".git/*" -x "*.DS_Store*" -z <<< "$OUTPUT"
