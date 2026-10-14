#!/usr/bin/env python3
"""Install dependencies and create local configuration without exposing credentials."""

import getpass
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info < (3, 10):
        print("Python 3.10+ is required.")
        return 1
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
            check=True,
        )
        env_path = ROOT / ".env"
        if not env_path.exists():
            key = getpass.getpass("OpenAI API key (leave blank to configure later): ").strip()
            config = (ROOT / ".env.example").read_text()
            config = config.replace("your_openai_api_key_here", key)
            config = config.replace(
                "PRESENTIQ_ACCESS_TOKEN=\n", f"PRESENTIQ_ACCESS_TOKEN={secrets.token_urlsafe(32)}\n"
            )
            with os.fdopen(
                os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w"
            ) as handle:
                handle.write(config)
            print(
                "Created .env. Keep PRESENTIQ_ACCESS_TOKEN private for researcher and API access."
            )
        else:
            print(
                "Existing .env preserved. PRESENTIQ_ACCESS_TOKEN controls researcher and API access."
            )
        subprocess.run([sys.executable, str(ROOT / "test_system.py")], check=True, cwd=ROOT)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Setup failed ({type(exc).__name__}).")
        return 1
    print("Setup complete. Run: streamlit run app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
