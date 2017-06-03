#!/usr/bin/env bash
# install dependencies
pip3 install -r requirements.txt --user

# setup commit hook
touch .git/hooks/pre-commit
echo "python3 -m 'nose'" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

