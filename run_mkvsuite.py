"""PyInstaller entry point (the package itself uses relative imports)."""
import sys

from mkvsuite.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
