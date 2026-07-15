from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from okf_validator.index import build_indexes, check_indexes, write_indexes

BUNDLE_ROOT = Path(__file__).resolve().parents[2] / "bundle"


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(body).lstrip(), encoding="utf-8")


def _write_doc(path: Path, type_: str, title: str, description: str) -> None:
    # `resource` satisfies Metric/DataSource's required field; harmless extra
    # key for every other type (ConceptBase allows extras).
    _write(
        path,
        f"""
        ---
        type: {type_}
        title: {title}
        description: {description}
        resource: dummy
        ---
        Body.
        """,
    )


def test_writes_index_grouped_by_type_with_relative_links(tmp_path: Path):
    root = tmp_path / "bundle"
    _write_doc(root / "metrics" / "requests_good.md", "Metric", "Good requests", "Good request counter.")
    _write_doc(root / "metrics" / "requests_total.md", "Metric", "Total requests", "Total request counter.")

    written = write_indexes(root)
    assert written == [root / "index.md", root / "metrics" / "index.md"]

    metrics_index = (root / "metrics" / "index.md").read_text(encoding="utf-8")
    assert metrics_index.startswith("# Metric")
    assert "[Good requests](requests_good.md) - Good request counter." in metrics_index
    assert "[Total requests](requests_total.md) - Total request counter." in metrics_index

    root_index = (root / "index.md").read_text(encoding="utf-8")
    assert "# Subdirectories" in root_index
    assert "[metrics](metrics/index.md)" in root_index


def test_single_child_description_is_reused_on_parent(tmp_path: Path):
    root = tmp_path / "bundle"
    _write_doc(root / "datasources" / "prometheus-prod.md", "DataSource", "Prometheus prod", "The only data source.")

    write_indexes(root)

    root_index = (root / "index.md").read_text(encoding="utf-8")
    assert "[datasources](datasources/index.md) - The only data source." in root_index


def test_multi_child_subdirectory_has_no_synthesized_description(tmp_path: Path):
    root = tmp_path / "bundle"
    _write_doc(root / "metrics" / "a.md", "Metric", "A", "Metric A.")
    _write_doc(root / "metrics" / "b.md", "Metric", "B", "Metric B.")

    write_indexes(root)

    root_index = (root / "index.md").read_text(encoding="utf-8")
    assert "[metrics](metrics/index.md)\n" in root_index


def test_skips_empty_and_invalid_only_directories(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "empty_dir").mkdir()
    _write(root / "bad_dir" / "broken.md", "no frontmatter here\n")

    written = write_indexes(root)
    assert written == []
    assert not (root / "empty_dir" / "index.md").exists()
    assert not (root / "bad_dir" / "index.md").exists()


def test_reserved_filenames_are_not_entries(tmp_path: Path):
    root = tmp_path / "bundle"
    _write_doc(root / "metrics" / "a.md", "Metric", "A", "Metric A.")
    _write(root / "metrics" / "index.md", "# stale\n")
    _write(root / "metrics" / "log.md", "# log\n")

    write_indexes(root)

    metrics_index = (root / "metrics" / "index.md").read_text(encoding="utf-8")
    assert "log.md" not in metrics_index
    assert "index.md" not in metrics_index


def test_check_reports_missing_and_stale_then_passes_after_write(tmp_path: Path):
    root = tmp_path / "bundle"
    _write_doc(root / "metrics" / "a.md", "Metric", "A", "Metric A.")

    stale = check_indexes(root)
    assert set(stale) == {root / "index.md", root / "metrics" / "index.md"}

    write_indexes(root)
    assert check_indexes(root) == []

    # Adding a second child also invalidates root/index.md: the "metrics"
    # subdirectory entry there loses its reused single-child description.
    _write_doc(root / "metrics" / "b.md", "Metric", "B", "Metric B.")
    assert set(check_indexes(root)) == {root / "index.md", root / "metrics" / "index.md"}


def test_multiline_description_is_flattened_to_one_line(tmp_path: Path):
    root = tmp_path / "bundle"
    _write(
        root / "alerts" / "a.md",
        """
        ---
        type: Widget
        title: A
        description: >
          Fires when the error budget

          is burning too fast.
        resource: dummy
        ---
        Body.
        """,
    )

    write_indexes(root)

    alerts_index = (root / "alerts" / "index.md").read_text(encoding="utf-8")
    assert alerts_index == (
        "# Widget\n\n* [A](a.md) - Fires when the error budget is burning too fast.\n"
    )


def test_build_indexes_does_not_touch_disk(tmp_path: Path):
    root = tmp_path / "bundle"
    _write_doc(root / "metrics" / "a.md", "Metric", "A", "Metric A.")

    computed = build_indexes(root)
    assert set(computed) == {root / "index.md", root / "metrics" / "index.md"}
    assert not (root / "index.md").exists()


def test_checkout_pilot_bundle_computes_indexes_without_touching_disk(tmp_path: Path):
    # Read-only against the real bundle/ -- must not call write_indexes here,
    # that would clobber the hand-authored bundle/index.md and bundle/log.md.
    computed = build_indexes(BUNDLE_ROOT)
    assert (BUNDLE_ROOT / "index.md") in computed
    assert computed[BUNDLE_ROOT / "metrics" / "index.md"].startswith("# Metric")
