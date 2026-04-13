import os
key = os.getenv("ANTHROPIC_API_KEY")
print("Using API key suffix:", key[-6:] if key else None)