#!/usr/bin/env bash
set -euo pipefail
# setup_pa.sh -- helper to prepare this project on PythonAnywhere
# Usage: upload this file to your project dir on PythonAnywhere, then run:
#   chmod +x setup_pa.sh
#   ./setup_pa.sh

PROJECT_DIR="$(pwd)"
HOME_DIR="${HOME:-/home/$(whoami)}"
VENV_DIR="${N0X_VENV:-$HOME_DIR/venvs/n0x}"

echo "Project dir: $PROJECT_DIR"
echo "Virtualenv: $VENV_DIR"

# Choose python binary (prefer 3.11, then 3.10, then python3)
if command -v python3.11 >/dev/null 2>&1; then
  PYTHON=python3.11
elif command -v python3.10 >/dev/null 2>&1; then
  PYTHON=python3.10
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  echo "No suitable python binary found (need python3.10+)." >&2
  exit 1
fi

echo "Using $PYTHON to create virtualenv..."
mkdir -p "$(dirname "$VENV_DIR")"
${PYTHON} -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  echo "Warning: requirements.txt not found in $PROJECT_DIR"
fi

# Ensure data dir exists and is writable by the app
mkdir -p "$PROJECT_DIR/data"
chmod 700 "$PROJECT_DIR/data"

# Create a .env.sample for local development (DO NOT COMMIT secrets)
cat > "$PROJECT_DIR/.env.sample" <<'EOF'
# Copy to .env for local development (keep .env in .gitignore)
INSTA_USER=
INSTA_PASS=
N0X_DEFAULT_CONTEXT=أنا ماسح إنستا ومبخش كتير
N0X_ENV=prod
EOF

echo
echo "Setup complete. Next manual steps:"
echo "- In PythonAnywhere Web tab set the Virtualenv path to: $VENV_DIR"
echo "- In PythonAnywhere Web -> Environment variables add: INSTA_USER and INSTA_PASS"
echo "- Make sure your WSGI file imports 'from main import app as application'"
echo
echo "To run locally for quick test (in this shell):"
echo "  source '$VENV_DIR/bin/activate'"
echo "  python main.py"

echo
echo "Reminder: Do NOT store passwords in source or commit them to git. Use Environment variables or OAuth tokens."
