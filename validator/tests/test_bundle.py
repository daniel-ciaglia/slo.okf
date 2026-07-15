"""Runs the validator against the checkout pilot bundle in strict mode.

This is the practical CI substitute while Gitea Actions/Woodpecker wiring is
deferred (see PLAN.md) -- `pytest` is the thing a contributor is expected to
run before pushing.
"""

from __future__ import annotations

from pathlib import Path

from okf_validator.cli import main

BUNDLE_ROOT = Path(__file__).resolve().parents[2] / "bundle"


def test_bundle_passes_strict(capsys):
    exit_code = main(["validate", str(BUNDLE_ROOT), "--strict"])
    captured = capsys.readouterr()
    assert exit_code == 0, captured.out
