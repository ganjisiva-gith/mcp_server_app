import os
import runpy
import sys

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
os.environ.setdefault("PYTHONHASHSEED", "0")

sys.dont_write_bytecode = True

if __name__ == "__main__":
    runpy.run_path("app.py", run_name="__main__")
