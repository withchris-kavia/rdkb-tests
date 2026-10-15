"""Supplemental L1 header contracts, not vendor HAL behavioral coverage."""

from itertools import product
from pathlib import Path
import shutil
import subprocess

import pytest

INCLUDE = Path(__file__).resolve().parents[2] / "rdkb-halif-bridge-util-348946/include"
CONFIGURATIONS = list(product((False, True), repeat=3))
CONFIG_IDS = [
    f"wifi{int(w)}-amenities{int(a)}-cbr2{int(c)}" for w, a, c in CONFIGURATIONS
]
API_TYPES = {
    "updateBridgeInfo": "int (*)(bridgeDetails *, char *, int, int)",
    "checkIfExists": "int (*)(char *)",
    "removeIfaceFromList": "void (*)(char *, const char *)",
    "checkIfExistsInBridge": "int (*)(char *, char *)",
    "HandlePreConfigVendor": "int (*)(bridgeDetails *, int)",
    "HandlePostConfigVendor": "int (*)(bridgeDetails *, int)",
    # C's empty parameter list is not a strict no-argument prototype.
    "getVendorIfaces": "char *(*)()",
}
FEATURE_SYMBOLS = (
    "MANAGE_WIFI_BRIDGE", "AMENITY_BRIDGE_2G",
    "AMENITY_BRIDGE_5G", "AMENITY_BRIDGE_6G",
)


def _probe(source, configuration):
    """Compile the actual headers without linking or executing vendor functions."""
    compiler = shutil.which("cc")
    assert compiler, "Contract checks require a GNU-compatible C11 compiler named cc"
    flags = [
        "-D" + macro for enabled, macro in zip(
            configuration,
            ("WIFI_MANAGE_SUPPORTED", "AMENITIES_NETWORK_ENABLED", "_CBR2_PRODUCT_REQ_"),
        ) if enabled
    ]
    return subprocess.run(
        [compiler, "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-fsyntax-only",
         "-I", str(INCLUDE), *flags, "-x", "c", "-"],
        input='#include "bridge_util_hal.h"\n' + source,
        text=True, capture_output=True, timeout=20, cwd=INCLUDE.parent,
    )


# PUBLIC_INTERFACE
@pytest.mark.parametrize("configuration", CONFIGURATIONS, ids=CONFIG_IDS)
def test_l1_api_types_across_feature_configurations(configuration):
    """Check all seven API types without function-pointer assignment conversions."""
    checks = "\n".join(
        f'_Static_assert(_Generic(&{api}, {ctype}: 1, default: 0), "{api} type");'
        for api, ctype in API_TYPES.items()
    )
    result = _probe(checks, configuration)
    assert result.returncode == 0, result.stdout + result.stderr


# PUBLIC_INTERFACE
@pytest.mark.parametrize("configuration", CONFIGURATIONS, ids=CONFIG_IDS)
@pytest.mark.parametrize("symbol", FEATURE_SYMBOLS)
def test_l1_conditional_symbol_visibility(configuration, symbol):
    """Check enabled presence and disabled absence with a valid control probe."""
    wifi, amenities, cbr2 = configuration
    enabled = wifi if symbol == "MANAGE_WIFI_BRIDGE" else amenities and not cbr2
    # A successful control excludes missing headers/tools as false absence evidence.
    control = _probe("enum Config control = PRIVATE_LAN;\n", configuration)
    assert control.returncode == 0, control.stdout + control.stderr
    result = _probe(f"enum Config probe = {symbol};\n", configuration)
    if enabled:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0, f"{symbol} unexpectedly exposed: {configuration}"
        assert symbol in result.stderr, result.stdout + result.stderr


# PUBLIC_INTERFACE
def test_l1_external_global_types_and_capacities():
    """Validate public globals via unevaluated expressions, without definitions."""
    scalar_types = {
        **dict.fromkeys((
            "DeviceMode", "MocaIsolation_Val", "need_wifi_gw_refresh",
            "need_switch_gw_refresh", "syncMembers", "BridgeOprInPropgress",
            "PORT2ENABLE", "ethWanEnabled",
        ), "int"),
        "logFp": "FILE *", "timeinfo": "struct tm *", "utc_time": "time_t",
    }
    checks = [
        f'_Static_assert(_Generic({name}, {ctype}: 1, default: 0), "{name} type");'
        for name, ctype in scalar_types.items()
    ]
    for name, size in (
        ("log_buff", 1024), ("log_msg_wtime", 1088),
        ("primaryBridgeName", 64), ("ethWanIfaceName", 64),
    ):
        checks.extend((
            f'_Static_assert(sizeof({name}) == {size}, "{name} capacity");',
            f'_Static_assert(_Generic(&{name}, char (*)[{size}]: 1, default: 0),'
            f' "{name} array type");',
        ))
    result = _probe("\n".join(checks), (False, False, False))
    assert result.returncode == 0, result.stdout + result.stderr
