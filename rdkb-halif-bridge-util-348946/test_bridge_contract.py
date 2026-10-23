"""Static checks of the real bridge-util headers; no vendor HAL is simulated."""
import itertools
from pathlib import Path
import shutil
import subprocess

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "rdkb-halif-bridge-util-348946"
SIGNATURES = {
    "updateBridgeInfo": ("int", "bridgeDetails *, char *, int, int"),
    "checkIfExists": ("int", "char *"),
    "removeIfaceFromList": ("void", "char *, const char *"),
    "checkIfExistsInBridge": ("int", "char *, char *"),
    "HandlePreConfigVendor": ("int", "bridgeDetails *, int"),
    "HandlePostConfigVendor": ("int", "bridgeDetails *, int"),
    # Preserve the actual unspecified C parameter list, not an invented (void).
    "getVendorIfaces": ("char *", ""),
}
CONSTANTS = {
    "TOTAL_IFLIST_SIZE": 1024, "BRIDGE_NAME_SIZE": 64, "IFACE_NAME_SIZE": 64,
    "IFLIST_SIZE": 256, "MAX_LOG_BUFF_SIZE": 1024, "TIMESTAMP": 64,
    "INTERFACE_EXIST": 0, "INTERFACE_NOT_EXIST": -1,
    "MAX_IF_NAME_SIZE": 16, "MAX_IP_ADDR_SIZE": 16, "MAX_BRIDGE_NAME_SIZE": 16,
}
ENUMS = {
    "PRIVATE_LAN": 1, "HOME_SECURITY": 2, "HOTSPOT_2G": 3, "HOTSPOT_5G": 4,
    "LOST_N_FOUND": 6, "HOTSPOT_SECURE_2G": 7, "HOTSPOT_SECURE_5G": 8,
    "MOCA_ISOLATION": 9, "MESH_BACKHAUL": 10, "ETH_BACKHAUL": 11, "MESH": 12,
    "MESH_WIFI_BACKHAUL_2G": 13, "MESH_WIFI_BACKHAUL_5G": 14,
    "MESH_ONBOARD": 18, "MESH_WIFI_ONBOARD_2G": 19,
    "IF_BRIDGE_BRIDGEUTIL": 1, "IF_VLAN_BRIDGEUTIL": 2,
    "IF_GRE_BRIDGEUTIL": 3, "IF_MOCA_BRIDGEUTIL": 4,
    "IF_WIFI_BRIDGEUTIL": 5, "IF_ETH_BRIDGEUTIL": 6, "IF_OTHER_BRIDGEUTIL": 7,
    "DELETE_BRIDGE": 0, "CREATE_BRIDGE": 1,
    "OTHER_IF_TYPE": 0, "BRIDGE_IF_TYPE": 1, "ETH_IF_TYPE": 2,
    "GRE_IF_TYPE": 3, "VLAN_IF_TYPE": 4,
    "IF_UP_CMD": 0, "IF_DOWN_CMD": 1, "IF_DELETE_CMD": 2, "BR_REMOVE_CMD": 3,
}
ARRAYS = [
    ("bridgeDetails", field, size)
    for field, size in [
        ("bridgeName", 64), ("vlan_name", 64), ("VirtualParentIfname", 64),
        ("ethIfList", 256), ("MoCAIfList", 256), ("GreIfList", 256),
        ("WiFiIfList", 256),
    ]
] + [
    ("Gateway_Config_Non_Ovs_Bridge", field, 16)
    for field in ["if_name", "inet_addr", "netmask", "gre_remote_inet_addr",
                  "gre_local_inet_addr", "parent_ifname", "parent_bridge"]
]
GLOBALS = {
    **{name: "int" for name in [
        "DeviceMode", "MocaIsolation_Val", "need_wifi_gw_refresh",
        "need_switch_gw_refresh", "syncMembers", "BridgeOprInPropgress",
        "PORT2ENABLE", "ethWanEnabled",
    ]},
    "logFp": "FILE *", "timeinfo": "struct tm *", "utc_time": "time_t",
}
GLOBAL_ARRAYS = {
    "log_buff": 1024, "log_msg_wtime": 1088,
    "primaryBridgeName": 64, "ethWanIfaceName": 64,
}


@pytest.fixture(scope="module")
# PUBLIC_INTERFACE
def compiler():
    """Require a real host GNU-compatible C compiler."""
    executable = shutil.which("cc")
    assert executable, "Install a compiler providing cc"
    return executable


def _compile(compiler, body, flags=()):
    return subprocess.run(
        [compiler, "-std=gnu11", "-Wall", "-Wextra", "-Werror",
         "-fsyntax-only", "-x", "c", "-I", str(SOURCE / "include"), *flags, "-"],
        input='#include "bridge_util_hal.h"\n#include "network_interface.h"\n' + body,
        capture_output=True, text=True, cwd=SOURCE, timeout=20,
    )


def _accept(compiler, body, flags=()):
    result = _compile(compiler, body, flags)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("name", SIGNATURES)
# PUBLIC_INTERFACE
def test_api_signature(compiler, name):
    """B-API: preserve the seven public function declaration types."""
    result, args = SIGNATURES[name]
    _accept(compiler, f"{result} (*contract_probe)({args}) = &{name};\n")


@pytest.mark.parametrize("name,value", {**CONSTANTS, **ENUMS}.items())
# PUBLIC_INTERFACE
def test_numeric_contract(compiler, name, value):
    """B-VALUE: preserve numeric macros and all unconditional enumerators."""
    _accept(compiler, f'_Static_assert({name} == ({value}), "{name}");\n')


@pytest.mark.parametrize("type_name,field,size", ARRAYS)
# PUBLIC_INTERFACE
def test_structure_buffer_capacity(compiler, type_name, field, size):
    """B-BUFFER: preserve declared member capacities, not runtime string safety."""
    _accept(compiler, f'_Static_assert(sizeof((({type_name} *)0)->{field}) == {size}, "{field}");\n')


@pytest.mark.parametrize("name,type_name", GLOBALS.items())
# PUBLIC_INTERFACE
def test_global_type(compiler, name, type_name):
    """B-GLOBAL: preserve extern scalar/pointer types without defining them."""
    _accept(compiler, f"{type_name} *contract_probe = &{name};\n")


@pytest.mark.parametrize("name,size", GLOBAL_ARRAYS.items())
# PUBLIC_INTERFACE
def test_global_array_extent(compiler, name, size):
    """B-GLOBAL: preserve extern character-array element type and extent."""
    _accept(compiler, f"char (*contract_probe)[{size}] = &{name};\n")


@pytest.mark.parametrize(
    "wifi,amenities,cbr", list(itertools.product([False, True], repeat=3)),
    ids=[f"wifi{int(w)}-amenities{int(a)}-cbr{int(c)}"
         for w, a, c in itertools.product([False, True], repeat=3)],
)
# PUBLIC_INTERFACE
def test_feature_views(compiler, wifi, amenities, cbr):
    """B-FEATURE: check gated enum presence and absence in every macro view."""
    flags = [
        f"-D{name}" for name, enabled in [
            ("WIFI_MANAGE_SUPPORTED", wifi),
            ("AMENITIES_NETWORK_ENABLED", amenities),
            ("_CBR2_PRODUCT_REQ_", cbr),
        ] if enabled
    ]
    _accept(compiler, "", flags)
    for symbol, value, available in [
        ("MANAGE_WIFI_BRIDGE", 17, wifi),
        ("AMENITY_BRIDGE_2G", 20, amenities and not cbr),
        ("AMENITY_BRIDGE_5G", 21, amenities and not cbr),
        ("AMENITY_BRIDGE_6G", 22, amenities and not cbr),
    ]:
        result = _compile(
            compiler, f'_Static_assert({symbol} == {value}, "{symbol}");\n', flags
        )
        if available:
            assert result.returncode == 0, result.stderr
        else:
            assert result.returncode != 0, f"{symbol} unexpectedly available"
            assert symbol in result.stderr, result.stderr


@pytest.mark.parametrize("header", ["bridge_util_hal.h", "network_interface.h"])
# PUBLIC_INTERFACE
def test_header_repeat_inclusion(compiler, header):
    """B-INCLUDE: each header is independently usable and repeat-includable."""
    result = subprocess.run(
        [compiler, "-std=gnu11", "-Wall", "-Wextra", "-Werror",
         "-fsyntax-only", "-x", "c", "-I", str(SOURCE / "include"), "-"],
        input=f'#include "{header}"\n#include "{header}"\nint contract_probe;\n',
        capture_output=True, text=True, cwd=SOURCE, timeout=20,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("body", [
    "int (*contract_probe)(char *, char *) = &removeIfaceFromList;\n",
    "int (*contract_probe)(bridgeDetails *, char *, int) = &updateBridgeInfo;\n",
    "char **contract_probe = &primaryBridgeName;\n",
], ids=["wrong-return", "wrong-argument-count", "array-is-not-pointer"])
# PUBLIC_INTERFACE
def test_incompatible_types_rejected(compiler, body):
    """B-NEGATIVE: incompatible consumer declarations must fail type checking."""
    result = _compile(compiler, body)
    assert result.returncode != 0, "Compiler accepted incompatible declaration"
    assert "error:" in result.stderr.lower(), result.stderr
