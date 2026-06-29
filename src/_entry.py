"""PyInstaller entry point for the noteker binary."""
import sys
from noteker.main import main

if __name__ == "__main__":
    sys.exit(main())
