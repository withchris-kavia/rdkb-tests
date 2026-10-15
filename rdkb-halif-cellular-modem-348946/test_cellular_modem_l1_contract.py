"""Compile-only cellular-modem HAL interface regression tests.

Run from the workspace root:
    python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/ -q

Prerequisites: Python 3, pytest, and a C11 compiler available as ``cc``.
Successful checks exit 0; pytest assertion failures exit 1. Compiler diagnostics
are included in failures. No hardware, credentials, or environment variables
are required.

Scope: signatures for all three public APIs, rejection of incompatible
signatures, status constants, and repeated header inclusion. These are interface
checks, NOT behavioral L1 verification. This checkout has no vendor HAL
implementation, UT shim, or per-repository stubs. Runtime success/failure paths,
NULL handling, and firmware buffer boundary behavior require that implementation
and isolated lower-level dependencies. The firmware API documents a minimum
128-byte buffer but has no size argument; undersized buffers must not be passed
to real hardware to simulate a safe invalid-input test.
"""

from pathlib import Path
import shutil
import subprocess

import pytest


_INCLUDE_DIR = (
    Path(__file__).resolve().parents[2]
    / "rdkb-halif-cellular-modem-348946"
    / "include"
)
_HEADER = "cellular_modem_hal_api.h"
_APIS = (
    ("Modem_FactoryReset", "int (*)(void)", "int (*)(char *)"),
    ("Modem_Reboot", "int (*)(void)", "int (*)(char *)"),
    ("Modem_Firmware_Version", "int (*)(char *)", "int (*)(const char *)"),
)


def _compile(source, cwd):
    """Check a C translation unit without linking or executing HAL functions."""
    compiler = shutil.which("cc")
    assert compiler is not None, "A C11 compiler available as cc is required"
    assert (_INCLUDE_DIR / _HEADER).is_file(), (
        f"Missing source HAL header: {_INCLUDE_DIR / _HEADER}"
    )
    # stdin avoids generated native test files; syntax-only needs no HAL library.
    return subprocess.run(
        [
            compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-fsyntax-only",
            "-I",
            str(_INCLUDE_DIR),
            "-x",
            "c",
            "-",
        ],
        input=source,
        text=True,
        capture_output=True,
        cwd=cwd,
        timeout=30,
        check=False,
    )


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "api,expected_type,incompatible_type", _APIS, ids=[api[0] for api in _APIS]
)
def test_public_api_signature(api, expected_type, incompatible_type, tmp_path):
    """Require the exact documented return and argument types for each API."""
    source = (
        f'#include "{_HEADER}"\n'
        f'_Static_assert(_Generic(&{api}, {expected_type}: 1, default: 0), '
        f'"signature mismatch: {api}");\n'
    )
    result = _compile(source, tmp_path)
    assert result.returncode == 0, (
        f"{api} no longer has signature {expected_type}\n"
        f"{result.stdout}\n{result.stderr}"
    )


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "api,expected_type,incompatible_type", _APIS, ids=[api[0] for api in _APIS]
)
def test_incompatible_api_signature_is_rejected(
    api, expected_type, incompatible_type, tmp_path
):
    """Ensure an incompatible caller contract fails at compile time."""
    # _Generic tests types portably, without compiler-specific warning text.
    diagnostic = f"incompatible signature accepted: {api}"
    source = (
        f'#include "{_HEADER}"\n'
        f'_Static_assert(_Generic(&{api}, {incompatible_type}: 1, default: 0), '
        f'"{diagnostic}");\n'
    )
    result = _compile(source, tmp_path)
    assert result.returncode != 0, (
        f"{api} unexpectedly matches incompatible type {incompatible_type}"
    )
    # Verify rejection is from the intended assertion, not an unrelated error.
    assert diagnostic in result.stderr, (
        f"Expected signature assertion diagnostic; got:\n{result.stderr}"
    )


# PUBLIC_INTERFACE
def test_status_constants_and_repeated_inclusion(tmp_path):
    """Require documented status values and a safely repeatable public include."""
    source = (
        f'#include "{_HEADER}"\n'
        f'#include "{_HEADER}"\n'
        '_Static_assert(STATUS_SUCCESS == 0, "success must be zero");\n'
        '_Static_assert(STATUS_FAILED == -1, "failure must be minus one");\n'
        '_Static_assert(STATUS_SUCCESS != STATUS_FAILED, '
        '"success and failure must be distinct");\n'
    )
    result = _compile(source, tmp_path)
    assert result.returncode == 0, (
        f"Header/status contract failed:\n{result.stdout}\n{result.stderr}"
    )
