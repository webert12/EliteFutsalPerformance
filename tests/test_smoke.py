from pathlib import Path

def test_files_present():
    root = Path(__file__).resolve().parents[1]
    assert (root/'main.py').exists()
    assert (root/'app/models/usuario.py').exists()
