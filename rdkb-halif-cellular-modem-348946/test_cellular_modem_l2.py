"""L2 integration tests for the real cellular-modem HAL and modem driver.

Run from the workspace root:
    python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/test_cellular_modem_l2.py --collect-only -q
    python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/test_cellular_modem_l2.py -q

Configuration must be requested from the user and supplied by the orchestrator
through the supported environment mechanism; this suite never reads/writes .env:
CELLULAR_MODEM_L2_ENABLED=1 explicitly authorizes read-only lab-device access.
CELLULAR_MODEM_HAL_LIBRARY is the absolute vendor shared-library path.
CELLULAR_MODEM_EXPECTED_FIRMWARE is the independently verified lab firmware.
CELLULAR_MODEM_L2_TIMEOUT_SECONDS optionally sets a harness deadline (default 30).

Prerequisites: Python 3, pytest, a compatible vendor build of
libhal_cellular_modem_hal_api.so and its dependencies, and a ready lab modem.
No implementation is supplied by the interface repository. Do not point these
tests at preset-return mocks. Do not run concurrently against the same modem:
the HAL specification does not promise thread safety.

Possible output (expected examples, not observed runs): configured tests pass
(exit 0); incorrect status, firmware, guard bytes, or a timeout fails (exit 1).
Without opt-in all tests skip; this is not behavioral verification. Pytest
exit codes 2/3/4/5 mean interruption/internal error/usage error/no tests.
Reset and factory reset are intentionally excluded: there is no documented
safe recovery or independent state-observation interface for those operations.
"""

import json
import math
import os
from pathlib import Path
import subprocess
import sys

import pytest


# Use a fresh process to bound native blocking calls and contain native crashes.
# This invokes the real ABI; it does not implement or mock any HAL behavior.
_PROBE = r"""
import ctypes
import json
import sys

library_path, capacity_text, reads_text = sys.argv[1:]
capacity = int(capacity_text)
reads = int(reads_text)
library = ctypes.CDLL(library_path)
getter = library.Modem_Firmware_Version
getter.argtypes = [ctypes.POINTER(ctypes.c_char)]
getter.restype = ctypes.c_int

guard_size = 16
results = []
for _ in range(reads):
    storage = (ctypes.c_ubyte * (capacity + 2 * guard_size))()
    ctypes.memset(ctypes.addressof(storage), 0xA5, ctypes.sizeof(storage))
    pointer = ctypes.cast(
        ctypes.addressof(storage) + guard_size,
        ctypes.POINTER(ctypes.c_char),
    )
    status = getter(pointer)
    raw = bytes(storage)
    payload = raw[guard_size:guard_size + capacity]
    results.append({
        "status": status,
        "terminated": b"\0" in payload,
        "firmware_hex": payload.split(b"\0", 1)[0].hex(),
        "prefix_intact": raw[:guard_size] == b"\xA5" * guard_size,
        "suffix_intact": raw[guard_size + capacity:] == b"\xA5" * guard_size,
    })
print("CELLULAR_MODEM_L2_RESULT=" + json.dumps(results), flush=True)
"""


@pytest.fixture(scope="module")
def _lab_configuration():
    """Require explicit lab access and validate configuration before native use."""
    if os.environ.get("CELLULAR_MODEM_L2_ENABLED") != "1":
        pytest.skip("L2 lab-device access requires CELLULAR_MODEM_L2_ENABLED=1")

    path = Path(os.environ.get("CELLULAR_MODEM_HAL_LIBRARY", ""))
    assert path.is_absolute() and path.is_file(), (
        "Supply CELLULAR_MODEM_HAL_LIBRARY as an existing absolute vendor library path"
    )
    expected = os.environ.get("CELLULAR_MODEM_EXPECTED_FIRMWARE", "")
    assert expected and "\0" not in expected, (
        "Supply independently verified CELLULAR_MODEM_EXPECTED_FIRMWARE"
    )
    expected_bytes = expected.encode("utf-8")
    assert len(expected_bytes) < 128, "Expected firmware must fit the 128-byte ABI buffer"
    try:
        timeout = float(os.environ.get("CELLULAR_MODEM_L2_TIMEOUT_SECONDS", "30"))
    except ValueError:
        pytest.fail("CELLULAR_MODEM_L2_TIMEOUT_SECONDS must be numeric")
    assert math.isfinite(timeout) and timeout > 0, "Harness timeout must be finite and positive"
    return path, expected_bytes, timeout


def _retrieve(configuration, capacity, reads):
    """Call the actual shared-library ABI serially with a bounded child lifetime."""
    library, expected, timeout = configuration
    try:
        completed = subprocess.run(
            [sys.executable, "-c", _PROBE, str(library), str(capacity), str(reads)],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"Firmware retrieval exceeded the configured {timeout}s harness deadline")

    assert completed.returncode == 0, (
        f"Native probe exited {completed.returncode}; stderr: {completed.stderr}"
    )
    records = [
        line.removeprefix("CELLULAR_MODEM_L2_RESULT=")
        for line in completed.stdout.splitlines()
        if line.startswith("CELLULAR_MODEM_L2_RESULT=")
    ]
    assert len(records) == 1, f"Missing or ambiguous probe result: {completed.stdout}"
    results = json.loads(records[0])
    assert len(results) == reads, "Probe did not report every requested read"
    for result in results:
        assert result["status"] == 0, f"Expected STATUS_SUCCESS: {result}"
        assert result["prefix_intact"], "HAL wrote before the caller's buffer"
        assert result["suffix_intact"], "HAL wrote beyond the caller's buffer"
        assert result["terminated"], "Firmware output lacks a NUL terminator"
        assert bytes.fromhex(result["firmware_hex"]) == expected, (
            f"Firmware differs from independent lab reference: {result}"
        )
    return results


# PUBLIC_INTERFACE
@pytest.mark.parametrize("capacity", [128, 256], ids=["minimum_buffer", "larger_buffer"])
def test_l2_firmware_matches_lab_reference(_lab_configuration, capacity):
    """Verify driver-backed firmware retrieval and caller-buffer boundaries."""
    _retrieve(_lab_configuration, capacity, reads=1)


# PUBLIC_INTERFACE
def test_l2_sequential_firmware_reads_are_consistent(_lab_configuration):
    """Verify repeated serial reads in one HAL process match the lab reference."""
    results = _retrieve(_lab_configuration, capacity=128, reads=2)
    assert results[0]["firmware_hex"] == results[1]["firmware_hex"], (
        "Firmware changed between consecutive read-only calls"
    )
