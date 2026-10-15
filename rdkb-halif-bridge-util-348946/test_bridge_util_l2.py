"""Opt-in, serial L2 tests against a real lab vendor library.

No bridge creation/deletion or vendor pre/post configuration is invoked.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

# Native crashes and hangs must not take down pytest. No public HAL is mocked.
_PROBE = r'''
import ctypes
import json
import sys

library, operation, payload = sys.argv[1:]
hal = ctypes.CDLL(library)
data = json.loads(payload)
if operation == "remove":
    fn = hal.removeIfaceFromList
    fn.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_char_p]
    fn.restype = None
    raw = data["text"].encode("ascii")
    storage = ctypes.create_string_buffer(raw, len(raw) + 1)
    fn(storage, data["remove"].encode("ascii"))
    result = storage.value.decode("ascii")
elif operation == "exists":
    fn = hal.checkIfExists
    fn.argtypes = [ctypes.c_char_p]
    fn.restype = ctypes.c_int
    result = fn(data["iface"].encode("ascii"))
elif operation == "member":
    fn = hal.checkIfExistsInBridge
    fn.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    fn.restype = ctypes.c_int
    result = fn(data["iface"].encode("ascii"), data["bridge"].encode("ascii"))
else:
    raise ValueError(operation)
print("BRIDGE_RESULT=" + json.dumps(result))
'''


@pytest.fixture
def _library():
    """Require explicit lab authorization before loading any vendor code."""
    # Request these variables via the supported runtime environment mechanism.
    if os.environ.get("BRIDGE_UTIL_L2_ENABLED") != "1":
        pytest.skip("L2 lab access requires BRIDGE_UTIL_L2_ENABLED=1")
    path = Path(os.environ.get("BRIDGE_UTIL_HAL_LIBRARY", ""))
    assert path.is_absolute() and path.is_file(), (
        "BRIDGE_UTIL_HAL_LIBRARY must name an existing absolute library path"
    )
    return str(path)


def _call(library, operation, payload):
    """Invoke a native call under a fixed harness deadline."""
    result = subprocess.run(
        [sys.executable, "-c", _PROBE, library, operation, json.dumps(payload)],
        cwd=Path(__file__).resolve().parent, text=True, capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"Native probe exit {result.returncode}: {result.stderr}"
    )
    lines = [line for line in result.stdout.splitlines()
             if line.startswith("BRIDGE_RESULT=")]
    assert len(lines) == 1, f"Missing/ambiguous probe result: {result.stdout}"
    return json.loads(lines[0].split("=", 1)[1])


def _name(variable):
    """Validate independently supplied Linux lab interface names."""
    value = os.environ.get(variable, "")
    assert value and value.isascii() and len(value) < 16, (
        f"{variable} must be a nonempty ASCII name shorter than 16 bytes"
    )
    assert not any(c.isspace() for c in value), f"{variable} contains whitespace"
    return value


# PUBLIC_INTERFACE
@pytest.mark.parametrize("text,remove,expected", [
    ("wl0 wl11 moca0 ath0 eth3", "moca0", ["wl0", "wl11", "ath0", "eth3"]),
    ("moca0 eth0", "moca0", ["eth0"]),
    ("eth0 moca0", "moca0", ["eth0"]),
    ("moca0", "moca0", []),
    ("", "moca0", []),
    ("eth0 eth01", "eth9", ["eth0", "eth01"]),
], ids=["middle", "first", "last", "only", "empty", "absent"])
def test_l2_remove_interface_from_list(_library, text, remove, expected):
    """Check removal order, edge positions, and absent-name no-op behavior."""
    actual = _call(_library, "remove", {"text": text, "remove": remove})
    assert actual.split() == expected
    if remove not in text.split():
        assert actual == text, "Absent interface must leave list unchanged"


# PUBLIC_INTERFACE
@pytest.mark.parametrize("variable,expected", [
    ("BRIDGE_UTIL_EXISTING_IFACE", 0),
    ("BRIDGE_UTIL_ABSENT_IFACE", -1),
], ids=["existing", "absent"])
def test_l2_interface_existence(_library, variable, expected):
    """Compare HAL status against independently verified lab topology."""
    iface = _name(variable)
    assert _call(_library, "exists", {"iface": iface}) == expected


# PUBLIC_INTERFACE
@pytest.mark.parametrize("variable,expected", [
    ("BRIDGE_UTIL_MEMBER_IFACE", 0),
    ("BRIDGE_UTIL_NONMEMBER_IFACE", -1),
], ids=["member", "nonmember"])
def test_l2_bridge_membership(_library, variable, expected):
    """Check membership without changing the independently configured bridge."""
    payload = {"iface": _name(variable), "bridge": _name("BRIDGE_UTIL_BRIDGE")}
    assert _call(_library, "member", payload) == expected
