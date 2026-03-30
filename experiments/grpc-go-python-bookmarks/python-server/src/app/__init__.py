from pathlib import Path
import sys

generated_root = Path(__file__).resolve().parent / "generated"
generated_root_str = str(generated_root)
if generated_root_str not in sys.path:
    sys.path.append(generated_root_str)
