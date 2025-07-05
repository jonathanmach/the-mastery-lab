# Experiment: Python Project Isolation with src Layout

This experiment tried to demonstrate Python project isolation using the `src/` layout.

We created two separate FastAPI projects using:

```sh
uv init --package project_a
uv init --package project_b # ended up testing poetry for project_b to reproduce my setup
```

The hypothesis was that the `src/` layout would prevent accidental imports across project boundaries, ensuring modularity and maintainability.

## Expected Behavior

By default, `project_b` cannot import from `project_a` directly (e.g. via `from project_a import something`), because `project_a/src` is not on the Python path.

## ⚠️ Bypassing Isolation

However, this isolation can be bypassed manually:

```python
import os, sys
sys.path.append(os.path.abspath("../project_a/src"))
from project_a import main
```

This approach allows access to `project_a` from `project_b`, but breaks the modularity, safety, and maintainability offered by the `src/` layout.
Isolation can be bypassed — but only because Python allows it and you’re taking manual control.
