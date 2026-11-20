
import importlib
import sys

MODULES = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "asyncpg",
    "greenlet",
    "pydantic",
    "pydantic_settings",
    "jose",
    "pwdlib",
    "pandas",
    "numpy",
]

print(f"Python: {sys.version}")
print("-" * 45)

failed = []

for module in MODULES:
    try:
        importlib.import_module(module)
        print(f"[OK] {module}")
    except ImportError as error:
        print(f"[ERRO] {module}: {error}")
        failed.append(module)

print("-" * 45)

if failed:
    print("Dependências em falta:", ", ".join(failed))
    sys.exit(1)

print("Ambiente validado com sucesso!")
