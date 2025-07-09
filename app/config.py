# === 1. config.py ===
import os

SESSION_SECRET = os.getenv("SESSION_SECRET", "supersecret")
if not SESSION_SECRET:
	raise ValueError("SESSION_SECRET environment variable must be set and non-empty.")