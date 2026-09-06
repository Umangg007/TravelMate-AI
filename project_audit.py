\
from pathlib import Path

ROOT = Path(__file__).resolve().parent

required = [
    "app/main.py",
    "app/streamlit_app.py",
    "src/__init__.py",
    "src/data_loader.py",
    "src/recommender.py",
    "src/itinerary.py",
    "src/utils.py",
    "requirements.txt",
    ".gitignore",
    ".env.example",
    "README.md",
]

print("=" * 60)
print("🌍 TravelMate AI - Project Structure Audit")
print("=" * 60)

missing = []
for item in required:
    path = ROOT / item
    if path.exists():
        print(f"✅ {item}")
    else:
        print(f"❌ {item}")
        missing.append(item)

env_path = ROOT / ".env"
if env_path.exists():
    print("⚠️  .env exists locally — keep it private and never commit it.")
else:
    print("ℹ️  .env not found locally. Create it from .env.example when needed.")

print()
if missing:
    print("❌ Audit failed. Missing files:")
    for item in missing:
        print(f"   - {item}")
else:
    print("🎉 Project structure audit passed.")
