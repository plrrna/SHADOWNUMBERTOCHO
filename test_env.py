import os
import sys

print("=" * 50)
print("Environment Test")
print("=" * 50)
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")
print(f"BOT_TOKEN exists: {'YES' if os.getenv('BOT_TOKEN') else 'NO'}")
print(f"BOT_TOKEN value length: {len(os.getenv('BOT_TOKEN', ''))}")
print(f"CRYPTO_PAY_TOKEN exists: {'YES' if os.getenv('CRYPTO_PAY_TOKEN') else 'NO'}")
print("=" * 50)

# Now try importing bot.main
print("Attempting to import bot.main...")
try:
    from bot import main
    print("SUCCESS: bot.main imported successfully!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
