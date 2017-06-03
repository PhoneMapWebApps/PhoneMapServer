pip3 install -r requirements.txt --user
touch .git/hooks/pre-commit
echo "python3 -m 'nose'" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
