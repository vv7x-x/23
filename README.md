n0x - Instagram DM Auto-Reply System

Overview
--------
`n0x` is a rule-based Instagram DM auto-reply system that learns an owner's
style per conversation and generates adaptive replies. It does NOT use any
external AI services and is designed to be deployable on PythonAnywhere.

Key features
- Per-conversation style profiles saved on disk
- Rule-based intent detection (no external models)
- Personality core: calm sarcastic Egyptian Gen-Z
- Anti-spam and WhatsApp-request handling
- Typing and seen simulation

Files
- `main.py` - Flask entrypoint with endpoints to receive messages.
- `memory_manager.py` - File-backed conversation and profile storage.
- `style_engine.py` - Analyze owner messages and compute style profiles.
- `intent_engine.py` - Rule-based intent detection.
- `response_engine.py` - Generate replies using templates and profiles.
- `personality_engine.py` - Apply base personality transformations.

Deploy on PythonAnywhere
-----------------------
1. Create a Python 3.10 (or 3.11) web app on PythonAnywhere.
2. Upload these files to your account or clone the repo.
3. Ensure `requirements.txt` is present and contains `Flask`.
4. Set the WSGI entry file to `main.py` and the application callable to `app`.
5. Create a `data/` directory in the same folder (the app will create subfolders).
6. Use the provided endpoints to integrate with your Instagram DM ingestion pipeline.

Notes
- The system never automatically shares the WhatsApp number. It tracks requests per-user and escalates sarcasm on repeated requests.
- This project is a demo foundation and may be extended with real Instagram integration, rate-limiting, and security hardening before public use.

Credentials and security
------------------------
- Never put your Instagram username/password directly in the source code or commit them to Git.
- Preferred: use environment variables on PythonAnywhere.

  1) Set environment variables in the PythonAnywhere Web tab (Environment variables):
	  - `INSTA_USER` = your Instagram username
	  - `INSTA_PASS` = your Instagram password
	  - Optional: `N0X_DEFAULT_CONTEXT` to override the default context phrase

  2) Or export them in a console session for testing (not persistent across web reloads):
	  ```bash
	  export INSTA_USER="your_username"
	  export INSTA_PASS="your_password"
	  ```

- In your code, read them securely via `config.get_instagram_credentials()`.

Example usage in code:
```python
from config import get_instagram_credentials
user, pwd = get_instagram_credentials()
# don't print or log `pwd`
```

OAuth / official API
---------------------
- If possible, prefer Instagram/Facebook Graph API and OAuth tokens instead of raw passwords. The Graph API provides long-lived access tokens and is compliant with platform policies.

Local development
-----------------
- For local dev you may use a `.env` file and `python-dotenv` to load environment variables, but keep `.env` in `.gitignore` and never push it to remote.
# 23