"""Genera capturas de la interfaz para revisión visual: python pruebas/capturas.py"""
import sys, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main([str(Path(__file__).parent / "test_capturas_manual.py"), "-q", "-s"]))
