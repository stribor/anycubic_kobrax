# Project Instructions

- After making code or documentation changes for a task, stage the changed files and create a git commit before finishing the task, unless the user explicitly asks not to commit.
- Keep commits focused on the task that was just completed.
- When adding or using `ATTR_*`, `CONF_*`, `SERVICE_*`, or other names from `custom_components/anycubic_kobrax/const.py`, always update the importing module's `from .const import (...)` list in the same change. Before committing, grep for the new name and run an import-oriented check where practical, because `py_compile` alone will not catch missing imports used during module initialization.
