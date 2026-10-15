"""L1 interface conformance checks; these do not exercise a vendor HAL."""
from pathlib import Path
import shutil
import subprocess

import pytest

INCLUDE = Path(__file__).resolve().parents[2] / "rdkb-halif-bridge-util-348946/include"
SIGNATURES = {
    "updateBridgeInfo": "int (*p)(bridgeDetails *, char *, int, int)",
    "checkIfExists": "int (*p)(char *)",
    "removeIfaceFromList": "void (*p)(char *, const char *)",
    "checkIfExistsInBridge": "int (*p)(char *, char *)",
    "HandlePreConfigVendor": "int (*p)(bridgeDetails *, int)",
    "HandlePostConfigVendor": "int (*p)(bridgeDetails *, int)",
    "getVendorIfaces": "char *(*p)(void)",
}


def _compile(source, flags=()):
    """Compile stdin without linking unresolved vendor functions."""
    compiler = shutil.which("cc")
    assert compiler, "L1 requires a C11 compiler named cc"
    result = subprocess.run(
        [compiler, "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-fsyntax-only",
         "-I", str(INCLUDE), *flags, "-x", "c", "-"],
        input=source, text=True, capture_output=True, timeout=20,
        cwd=INCLUDE.parent,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# PUBLIC_INTERFACE
@pytest.mark.parametrize("api", SIGNATURES)
def test_l1_public_api_signature(api):
    """Verify each actual declaration accepts its documented pointer type."""
    _compile(
        '#include "bridge_util_hal.h"\n'
        f"void probe(void) {{ {SIGNATURES[api]} = {api}; (void)p; }}\n"
    )


# PUBLIC_INTERFACE
@pytest.mark.parametrize("field,size", [
    ("bridgeName", 64), ("vlan_name", 64), ("VirtualParentIfname", 64),
    ("ethIfList", 256), ("MoCAIfList", 256), ("GreIfList", 256),
    ("WiFiIfList", 256),
])
def test_l1_bridge_buffer_capacity(field, size):
    """Check fixed caller-buffer capacities, including terminator storage."""
    _compile(
        '#include "bridge_util_hal.h"\n'
        f'_Static_assert(sizeof(((bridgeDetails *)0)->{field}) == {size},'
        ' "bridge buffer capacity changed");\n'
    )


# PUBLIC_INTERFACE
def test_l1_network_contract():
    """Check independent network-header enums, buffers, and include guards."""
    _compile(r'''
#include "network_interface.h"
#include "network_interface.h"
#include "bridge_util_hal.h"
#include "bridge_util_hal.h"
#define CHECK(expr) _Static_assert((expr), #expr)
CHECK(MAX_IF_NAME_SIZE == 16);
CHECK(MAX_IP_ADDR_SIZE == 16);
CHECK(MAX_BRIDGE_NAME_SIZE == 16);
CHECK(INTERFACE_EXIST == 0);
CHECK(INTERFACE_NOT_EXIST == -1);
CHECK(DELETE_BRIDGE == 0 && CREATE_BRIDGE == 1);
CHECK(IF_BRIDGE_BRIDGEUTIL == 1 && IF_OTHER_BRIDGEUTIL == 7);
CHECK(OTHER_IF_TYPE == 0 && BRIDGE_IF_TYPE == 1 && ETH_IF_TYPE == 2);
CHECK(GRE_IF_TYPE == 3 && VLAN_IF_TYPE == 4);
CHECK(IF_UP_CMD == 0 && IF_DOWN_CMD == 1);
CHECK(IF_DELETE_CMD == 2 && BR_REMOVE_CMD == 3);
CHECK(sizeof(((Gateway_Config_Non_Ovs_Bridge *)0)->if_name) == 16);
CHECK(sizeof(((Gateway_Config_Non_Ovs_Bridge *)0)->inet_addr) == 16);
CHECK(sizeof(((Gateway_Config_Non_Ovs_Bridge *)0)->netmask) == 16);
CHECK(sizeof(((Gateway_Config_Non_Ovs_Bridge *)0)->gre_remote_inet_addr) == 16);
CHECK(sizeof(((Gateway_Config_Non_Ovs_Bridge *)0)->gre_local_inet_addr) == 16);
CHECK(sizeof(((Gateway_Config_Non_Ovs_Bridge *)0)->parent_ifname) == 16);
CHECK(sizeof(((Gateway_Config_Non_Ovs_Bridge *)0)->parent_bridge) == 16);
''')


# PUBLIC_INTERFACE
@pytest.mark.parametrize("wifi,amenities,cbr2", [
    (w, a, c) for w in (False, True) for a in (False, True)
    for c in (False, True)
])
def test_l1_feature_configuration(wifi, amenities, cbr2):
    """Verify configuration values across all documented feature combinations."""
    flags = [
        "-D" + name for enabled, name in [
            (wifi, "WIFI_MANAGE_SUPPORTED"),
            (amenities, "AMENITIES_NETWORK_ENABLED"),
            (cbr2, "_CBR2_PRODUCT_REQ_"),
        ] if enabled
    ]
    values = {
        "PRIVATE_LAN": 1, "HOME_SECURITY": 2, "HOTSPOT_2G": 3,
        "HOTSPOT_5G": 4, "LOST_N_FOUND": 6, "HOTSPOT_SECURE_2G": 7,
        "HOTSPOT_SECURE_5G": 8, "MOCA_ISOLATION": 9, "MESH_BACKHAUL": 10,
        "ETH_BACKHAUL": 11, "MESH": 12, "MESH_WIFI_BACKHAUL_2G": 13,
        "MESH_WIFI_BACKHAUL_5G": 14, "MESH_ONBOARD": 18,
        "MESH_WIFI_ONBOARD_2G": 19,
    }
    if wifi:
        values["MANAGE_WIFI_BRIDGE"] = 17
    if amenities and not cbr2:
        values.update(AMENITY_BRIDGE_2G=20, AMENITY_BRIDGE_5G=21,
                      AMENITY_BRIDGE_6G=22)
    checks = "\n".join(
        f'_Static_assert({name} == {value}, "{name} changed");'
        for name, value in values.items()
    )
    _compile('#include "bridge_util_hal.h"\n' + checks, flags)
