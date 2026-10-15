"""Regression tests for the skill runner, not HAL behavioral coverage."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "skills/rdkb_hal_l1_suite_builder/scripts/run_suite.py"
SPEC = importlib.util.spec_from_file_location("hal_l1_runner", SCRIPT)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


@pytest.fixture
# PUBLIC_INTERFACE
def suite(tmp_path):
    """Return a minimal local manifest and workspace for runner contract tests."""
    repo = tmp_path / "rdkb-halif-fixture"
    repo.mkdir()
    (repo / "hal.h").write_text("int api(void);\n")
    (repo / "shim.c").write_text("/* runner fixture, not a HAL mock */\n")
    destination = tmp_path / "rdkb-tests" / repo.name
    destination.mkdir(parents=True)
    xml = destination / "results.xml"
    document = '<testsuite><testcase name="api_positive_valid"/></testsuite>'
    config = {
        "repository": repo.name, "framework": "native-fixture",
        "headers": ["hal.h"], "support": [f"{repo.name}/shim.c"],
        "build": [sys.executable, "-c", "pass"],
        "run": [sys.executable, "-c",
                f"from pathlib import Path; Path({str(xml)!r}).write_text({document!r})"],
        "junit": "results.xml", "timeout_seconds": 10,
        "apis": [{"name": "api", "signature": "int api(void)",
                  "axes": {"positive": {"tests": ["api_positive_valid"]},
                           "negative": {"reason": "No parameters"},
                           "boundary": {"reason": "No numeric parameters"},
                           "error_return": {"reason": "Blocked: fixture has no HAL implementation"}}}],
    }
    manifest = destination / "manifest.json"
    manifest.write_text(json.dumps(config))
    return tmp_path, manifest, config, destination


def _save(suite):
    """Persist fixture config mutations before invoking the actual runner."""
    suite[1].write_text(json.dumps(suite[2]))


# PUBLIC_INTERFACE
def test_success_and_resume(suite):
    """Verify fresh evidence, reported gaps, and resume rerunning with a new ID."""
    workspace, manifest, _, destination = suite
    assert RUNNER.run_suite(manifest, workspace) == 0
    first = json.loads((destination / "hal_l1_report.json").read_text())
    assert first["totals"] == {"inventory": 1, "tests_written": 1, "passing": 1, "pass_rate": 1.0}
    assert first["apis"][0]["axes"]["error_return"]["reason"].startswith("Blocked")
    assert RUNNER.run_suite(manifest, workspace, resume=True) == 0
    second = json.loads((destination / "hal_l1_report.json").read_text())
    assert first["run_id"] != second["run_id"]
    assert len(second["commands"]) == 2


# PUBLIC_INTERFACE
def test_stale_results_not_reused(suite):
    """Verify a successful exit without fresh XML cannot inherit a prior pass."""
    workspace, manifest, config, destination = suite
    (destination / "results.xml").write_text('<testsuite><testcase name="api_positive_valid"/></testsuite>')
    config["run"] = [sys.executable, "-c", "pass"]
    _save(suite)
    assert RUNNER.run_suite(manifest, workspace) == 1
    report = json.loads((destination / "hal_l1_report.json").read_text())
    assert report["totals"]["passing"] == 0
    assert "FileNotFoundError" in report["error"]


@pytest.mark.parametrize("element", ["failure", "error", "skipped"])
# PUBLIC_INTERFACE
def test_nonpassing_evidence(suite, element):
    """Verify failures, native errors and skips never become passing coverage."""
    workspace, manifest, config, destination = suite
    document = f'<testsuite><testcase name="api_positive_valid"><{element}/></testcase></testsuite>'
    config["run"][-1] = f"from pathlib import Path; Path({str(destination / 'results.xml')!r}).write_text({document!r})"
    _save(suite)
    assert RUNNER.run_suite(manifest, workspace) == 1
    report = json.loads((destination / "hal_l1_report.json").read_text())
    assert report["totals"]["passing"] == 0


@pytest.mark.parametrize("document", [
    "<bad", "<testsuite/>",
    '<testsuite><testcase name="x"/><testcase name="x"/></testsuite>',
])
# PUBLIC_INTERFACE
def test_invalid_evidence(suite, document):
    """Verify malformed, empty and duplicate JUnit evidence fails safely."""
    workspace, manifest, config, destination = suite
    config["run"][-1] = f"from pathlib import Path; Path({str(destination / 'results.xml')!r}).write_text({document!r})"
    _save(suite)
    assert RUNNER.run_suite(manifest, workspace) == 1


@pytest.mark.parametrize("key,value", [
    ("headers", ["../outside.h"]), ("timeout_seconds", 0),
    ("timeout_seconds", float("nan")), ("build", "echo unsafe"),
    ("support", []), ("junit", "../outside.xml"),
])
# PUBLIC_INTERFACE
def test_invalid_configuration(suite, key, value):
    """Verify unsafe paths, missing support and invalid command inputs are rejected."""
    workspace, manifest, config, _ = suite
    config[key] = value
    _save(suite)
    with pytest.raises(ValueError):
        RUNNER.run_suite(manifest, workspace)


# PUBLIC_INTERFACE
def test_header_change_rejects_resume(suite):
    """Verify changed public declarations invalidate prior checkpoint compatibility."""
    workspace, manifest, config, _ = suite
    assert RUNNER.run_suite(manifest, workspace) == 0
    (workspace / config["repository"] / "hal.h").write_text("int changed(void);\n")
    with pytest.raises(ValueError, match="headers changed"):
        RUNNER.run_suite(manifest, workspace, resume=True)


# PUBLIC_INTERFACE
def test_build_failure_stops_run(suite):
    """Verify failed builds retain diagnostics and never execute the run command."""
    workspace, manifest, config, destination = suite
    config["build"] = [sys.executable, "-c", "import sys; print('compile failure'); sys.exit(3)"]
    _save(suite)
    assert RUNNER.run_suite(manifest, workspace) == 1
    state = json.loads((destination / "hal_l1_progress.json").read_text())
    assert len(state["commands"]) == 1
    assert state["commands"][0]["returncode"] == 3
    assert "compile failure" in Path(state["commands"][0]["log"]).read_text()


# PUBLIC_INTERFACE
def test_nonzero_run_preserves_case_evidence(suite):
    """Verify native assertion exits retain case-level XML failure diagnostics."""
    workspace, manifest, config, destination = suite
    document = '<testsuite><testcase name="api_positive_valid"><failure/></testcase></testsuite>'
    config["run"][-1] = (
        f"from pathlib import Path; Path({str(destination / 'results.xml')!r}).write_text({document!r}); "
        "import sys; sys.exit(1)"
    )
    _save(suite)
    assert RUNNER.run_suite(manifest, workspace) == 1
    report = json.loads((destination / "hal_l1_report.json").read_text())
    assert report["apis"][0]["axes"]["positive"]["tests"]["api_positive_valid"] == "failed"
    assert "run exited 1" in report["error"]


@pytest.mark.parametrize("failure", ["timeout", "interrupt", "missing"])
# PUBLIC_INTERFACE
def test_execution_boundaries(suite, monkeypatch, failure):
    """Verify timeout, interruption and missing executables persist failure state."""
    workspace, manifest, _, destination = suite

    def fail(*args, **kwargs):
        """Simulate a subprocess boundary error without sleeps or hardware access."""
        if failure == "timeout":
            raise RUNNER.subprocess.TimeoutExpired(args[0], 10)
        if failure == "interrupt":
            raise KeyboardInterrupt()
        raise FileNotFoundError("missing executable")

    monkeypatch.setattr(RUNNER.subprocess, "run", fail)
    assert RUNNER.run_suite(manifest, workspace) == 1
    state = json.loads((destination / "hal_l1_progress.json").read_text())
    assert state["stage"] == ("interrupted" if failure == "interrupt" else "failed")
    assert state["error"]
