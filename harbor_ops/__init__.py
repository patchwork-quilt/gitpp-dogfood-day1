"""harbor-ops — a small ferry-operations CLI.

The operations state it reports (release freeze, on-call primary,
feature flags, timetable season) is not stored in the program. It is
derived from the git.pp records under ``.gitpp/records/`` by the fold;
``harbor_ops/derived-state.json`` is the generated snapshot the CLI
reads. Regenerate it with ``python3 tools/derive.py``.
"""

__version__ = "0.2.0"
