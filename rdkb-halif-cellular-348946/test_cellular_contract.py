"""Compile-time contract regression tests; these do not execute a vendor HAL."""
from pathlib import Path
import re
import shutil
import subprocess

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "rdkb-halif-cellular-348946"
HEADER = SOURCE / "include" / "cellular_hal.h"

# Frozen independently of the header at execution time, so API drift fails.
SIGNATURES = {
    "IsModemDevicePresent": ("unsigned int", "void"),
    "init": ("int", "CellularContextInitInputStruct *"),
    "open_device": ("int", "CellularDeviceContextCBStruct *"),
    "IsModemControlInterfaceOpened": ("unsigned char", "void"),
    "select_device_slot": ("int", "cellular_device_slot_status_api_callback"),
    "sim_power_enable": ("int", "unsigned int, unsigned char"),
    "get_total_no_of_uicc_slots": ("int", "unsigned int *"),
    "get_uicc_slot_info": ("int", "unsigned int, CellularUICCSlotInfoStruct *"),
    "get_active_card_status": ("int", "CellularUICCStatus_t *"),
    "monitor_device_registration": ("int", "cellular_device_registration_status_callback"),
    "profile_create": ("int", "CellularProfileStruct *, cellular_device_profile_status_api_callback"),
    "profile_delete": ("int", "CellularProfileStruct *, cellular_device_profile_status_api_callback"),
    "profile_modify": ("int", "CellularProfileStruct *, cellular_device_profile_status_api_callback"),
    "get_profile_list": ("int", "CellularProfileStruct **, int *"),
    "start_network": ("int", "CellularNetworkIPType_t, CellularProfileStruct *, CellularNetworkCBStruct *"),
    "stop_network": ("int", "CellularNetworkIPType_t"),
    "get_signal_info": ("int", "CellularSignalInfoStruct *"),
    "get_cell_location_info": ("int", "CellLocationInfoStruct *"),
    "set_modem_operating_configuration": ("int", "CellularModemOperatingConfiguration_t"),
    "get_device_imei": ("int", "char *"),
    "get_device_imei_sv": ("int", "char *"),
    "get_modem_current_iccid": ("int", "char *"),
    "get_modem_current_msisdn": ("int", "char *"),
    "get_packet_statistics": ("int", "CellularPacketStatsStruct *"),
    "get_current_modem_interface_status": ("int", "CellularInterfaceStatus_t *"),
    "set_modem_network_attach": ("int", "void"),
    "set_modem_network_detach": ("int", "void"),
    "get_modem_firmware_version": ("int", "char *"),
    "get_current_plmn_information": ("int", "CellularCurrentPlmnInfoStruct *"),
    "get_available_networks_information": ("int", "CellularNetworkScanResultInfoStruct **, unsigned int *"),
    "get_modem_preferred_radio_technology": ("int", "char *"),
    "set_modem_preferred_radio_technology": ("int", "char *"),
    "get_modem_current_radio_technology": ("int", "char *"),
    "get_modem_supported_radio_technology": ("int", "char *"),
    "modem_factory_reset": ("int", "void"),
    "modem_reset": ("int", "void"),
}

CONSTANTS = {
    "RETURN_OK": 0, "RETURN_ERROR": -1, "TRUE": 1, "FALSE": 0,
    "BUFLEN_8": 8, "BUFLEN_32": 32, "BUFLEN_64": 64,
    "BUFLEN_128": 128, "BUFLEN_256": 256,
    "CELLULAR_PROFILE_ID_UNKNOWN": -1, "CELLULAR_SLOT_ID_UNKNOWN": -1,
    "CELLULAR_PDP_CONTEXT_UNKNOWN": -1,
    "CELLULAR_PACKET_DATA_INVALID_HANDLE": 0xFFFFFFFF,
}

ARRAYS = [
    ("CellularProfileStruct", "ProfileName", 64),
    ("CellularProfileStruct", "APN", 64),
    ("CellularProfileStruct", "Username", 256),
    ("CellularProfileStruct", "Password", 256),
    ("CellularProfileStruct", "Proxy", 45),
    ("CellularIPStruct", "WANIFName", 16),
    ("CellularIPStruct", "IPAddress", 128),
    ("CellularIPStruct", "SubnetMask", 128),
    ("CellularIPStruct", "DefaultGateWay", 128),
    ("CellularIPStruct", "DNSServer1", 128),
    ("CellularIPStruct", "DNSServer2", 128),
    ("CellularIPStruct", "Domains", 256),
    ("CellularUICCSlotInfoStruct", "MnoName", 32),
    ("CellularUICCSlotInfoStruct", "iccid", 20),
    ("CellularUICCSlotInfoStruct", "msisdn", 20),
    ("CellularCurrentPlmnInfoStruct", "plmn_name", 32),
    ("CellularNetworkScanResultInfoStruct", "network_name", 32),
]

ENUMS = {
    "CellularInterfaceStatus_t": (1, "IF_UP IF_DOWN IF_UNKNOWN IF_DORMANT IF_NOTPRESENT IF_LOWERLAYERDOWN IF_ERROR"),
    "CellularIpFamilyPref_t": (1, "IP_FAMILY_UNKNOWN IP_FAMILY_IPV4 IP_FAMILY_IPV6 IP_FAMILY_IPV4_IPV6"),
    "CellularPrefAccessTechnology_t": (1, "PREF_GPRS PREF_EDGE PREF_UMTS PREF_UMTSHSPA PREF_CDMA2000OneX PREF_CDMA2000HRPD PREF_LTE PREF_NR"),
    "CellularPDPType_t": (0, "CELLULAR_PDP_TYPE_IPV4 CELLULAR_PDP_TYPE_PPP CELLULAR_PDP_TYPE_IPV6 CELLULAR_PDP_TYPE_IPV4_OR_IPV6"),
    "CellularPDPAuthentication_t": (0, "CELLULAR_PDP_AUTHENTICATION_NONE CELLULAR_PDP_AUTHENTICATION_PAP CELLULAR_PDP_AUTHENTICATION_CHAP"),
    "CellularProfileType_t": (0, "CELLULAR_PROFILE_TYPE_3GPP CELLULAR_PROFILE_TYPE_3GPP2"),
    "CellularPDPNetworkConfig_t": (1, "CELLULAR_PDP_NETWORK_CONFIG_NAS CELLULAR_PDP_NETWORK_CONFIG_DHCP"),
    "CellularModemOperatingConfiguration_t": (1, "CELLULAR_MODEM_SET_ONLINE CELLULAR_MODEM_SET_OFFLINE CELLULAR_MODEM_SET_LOW_POWER_MODE CELLULAR_MODEM_SET_RESET CELLULAR_MODEM_SET_FACTORY_RESET"),
    "CellularModemRegisteredServiceType_t": (0, "CELLULAR_MODEM_REGISTERED_SERVICE_NONE CELLULAR_MODEM_REGISTERED_SERVICE_PS CELLULAR_MODEM_REGISTERED_SERVICE_CS CELLULAR_MODEM_REGISTERED_SERVICE_CS_PS"),
    "CellularRegistrationStatus_t": (1, "DEVICE_REGISTERED DEVICE_NOT_REGISTERED"),
    "CellularNetworkIPType_t": (0, "CELLULAR_NETWORK_IP_FAMILY_UNKNOWN CELLULAR_NETWORK_IP_FAMILY_IPV4 CELLULAR_NETWORK_IP_FAMILY_IPV6 CELLULAR_NETWORK_IP_FAMILY_UNSPECIFIED"),
    "CellularUICCFormFactor_t": (0, "CELLULAR_UICC_FORM_FACTOR_1FF CELLULAR_UICC_FORM_FACTOR_2FF CELLULAR_UICC_FORM_FACTOR_3FF CELLULAR_UICC_FORM_FACTOR_4FF"),
    "CellularUICCStatus_t": (0, "CELLULAR_UICC_STATUS_VALID CELLULAR_UICC_STATUS_BLOCKED CELLULAR_UICC_STATUS_ERROR CELLULAR_UICC_STATUS_EMPTY"),
    "CellularUICCApplication_t": (0, "CELLULAR_UICC_APPLICATION_USIM CELLULAR_UICC_APPLICATION_ISIM CELLULAR_UICC_APPLICATION_ESIM"),
    "CellularDeviceDetectionStatus_t": (1, "DEVICE_DETECTED DEVICE_REMOVED"),
    "CellularDeviceOpenStatus_t": (1, "DEVICE_OPEN_STATUS_NOT_READY DEVICE_OPEN_STATUS_INPROGRESS DEVICE_OPEN_STATUS_READY"),
    "CellularDeviceSlotStatus_t": (1, "DEVICE_SLOT_STATUS_NOT_READY DEVICE_SLOT_STATUS_SELECTING DEVICE_SLOT_STATUS_READY"),
    "CellularDeviceNASStatus_t": (1, "DEVICE_NAS_STATUS_NOT_REGISTERED DEVICE_NAS_STATUS_REGISTERING DEVICE_NAS_STATUS_REGISTERED"),
    "CellularDeviceNASRoamingStatus_t": (1, "DEVICE_NAS_STATUS_ROAMING_OFF DEVICE_NAS_STATUS_ROAMING_ON"),
    "CellularContextProfileStatus_t": (1, "PROFILE_STATUS_INACTIVE PROFILE_STATUS_ACTIVE"),
    "CellularDeviceProfileSelectionStatus_t": (1, "DEVICE_PROFILE_STATUS_NOT_READY DEVICE_PROFILE_STATUS_CONFIGURING DEVICE_PROFILE_STATUS_READY DEVICE_PROFILE_STATUS_DELETED"),
    "CellularDeviceIPReadyStatus_t": (1, "DEVICE_NETWORK_IP_NOT_READY DEVICE_NETWORK_IP_READY"),
    "CellularNetworkPacketStatus_t": (1, "DEVICE_NETWORK_STATUS_DISCONNECTED DEVICE_NETWORK_STATUS_CONNECTED"),
}

CALLBACKS = {
    "cellular_device_open_status_api_callback": "char *, char *, CellularDeviceOpenStatus_t, CellularModemOperatingConfiguration_t",
    "cellular_device_removed_status_api_callback": "char *, CellularDeviceDetectionStatus_t",
    "cellular_device_slot_status_api_callback": "char *, char *, int, CellularDeviceSlotStatus_t",
    "cellular_device_registration_status_callback": "CellularDeviceNASStatus_t, CellularDeviceNASRoamingStatus_t, CellularModemRegisteredServiceType_t",
    "cellular_device_profile_status_api_callback": "char *, CellularPDPType_t, CellularDeviceProfileSelectionStatus_t",
    "cellular_network_packet_service_status_api_callback": "char *, CellularNetworkIPType_t, CellularNetworkPacketStatus_t",
    "cellular_device_network_ip_ready_api_callback": "CellularIPStruct *, CellularDeviceIPReadyStatus_t",
}


@pytest.fixture(scope="module")
# PUBLIC_INTERFACE
def compiler():
    """Require a host C11 compiler; missing tooling is an error, not a pass."""
    executable = shutil.which("cc")
    assert executable, "Install a C11 compiler providing cc before running this suite"
    return executable


def _compile(compiler, body, defines=()):
    result = subprocess.run(
        [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
         "-fsyntax-only", "-x", "c", "-I", str(HEADER.parent), *defines, "-"],
        input='#include "cellular_hal.h"\n#include "cellular_hal.h"\n' + body,
        text=True, capture_output=True, cwd=SOURCE, timeout=20,
    )
    return result


def _assert_compiles(compiler, body, defines=()):
    result = _compile(compiler, body, defines)
    assert result.returncode == 0, f"Contract compilation failed:\n{result.stderr}"


# PUBLIC_INTERFACE
def test_api_inventory():
    """C-API: detect added/removed APIs rather than silently missing new APIs."""
    text = re.sub(r"/\*.*?\*/", "", HEADER.read_text(), flags=re.S)
    found = set(re.findall(r"\b(cellular_hal_\w+)\s*\([^;{}]*\)\s*;", text))
    assert found == {"cellular_hal_" + name for name in SIGNATURES}


@pytest.mark.parametrize("name", SIGNATURES)
# PUBLIC_INTERFACE
def test_api_signature(compiler, name):
    """C-API: pin return types and every parameter without executing the HAL."""
    return_type, arguments = SIGNATURES[name]
    _assert_compiles(
        compiler,
        f"{return_type} (*contract_probe)({arguments}) = &cellular_hal_{name};\n",
    )


@pytest.mark.parametrize("name,value", CONSTANTS.items())
# PUBLIC_INTERFACE
def test_constant_value(compiler, name, value):
    """C-CONSTANT: pin success/error, unknown IDs, buffer macros and handle."""
    _assert_compiles(compiler, f'_Static_assert({name} == ({value}), "{name}");\n')


@pytest.mark.parametrize("type_name,member,size", ARRAYS)
# PUBLIC_INTERFACE
def test_buffer_capacity(compiler, type_name, member, size):
    """C-BUFFER: pin declared capacity; not runtime termination or overflow."""
    _assert_compiles(
        compiler,
        f'_Static_assert(sizeof((({type_name} *)0)->{member}) == {size}, "{member}");\n',
    )


@pytest.mark.parametrize("type_name", ENUMS)
# PUBLIC_INTERFACE
def test_enum_values(compiler, type_name):
    """C-ENUM: pin every enumerator value in each documented enum."""
    start, members = ENUMS[type_name]
    body = f"{type_name} contract_probe;\n"
    body += "".join(
        f'_Static_assert({member} == {value}, "{member}");\n'
        for value, member in enumerate(members.split(), start)
    )
    _assert_compiles(compiler, body)


@pytest.mark.parametrize("name,arguments", CALLBACKS.items())
# PUBLIC_INTERFACE
def test_callback_signature(compiler, name, arguments):
    """C-CALLBACK: check callback argument/return compatibility both ways."""
    _assert_compiles(
        compiler,
        f"int (*contract_expected)({arguments});\n"
        f"{name} contract_actual;\n"
        "void contract_probe(void) {\n"
        "contract_expected = contract_actual;\n"
        "contract_actual = contract_expected;\n}\n",
    )


@pytest.mark.parametrize("lite", [False, True], ids=["full", "lite"])
# PUBLIC_INTERFACE
def test_qmi_build_variant(compiler, lite):
    """C-VARIANT: QMI is default but not implicitly enabled for lite builds."""
    condition = "#ifdef" if lite else "#ifndef"
    _assert_compiles(
        compiler,
        f"{condition} QMI_SUPPORT\n#error Unexpected QMI_SUPPORT selection\n#endif\n",
        ("-DCELLULAR_MGR_LITE",) if lite else (),
    )


@pytest.mark.parametrize("name", ["TRUE", "FALSE", "BUFLEN_8", "BUFLEN_32",
                                  "BUFLEN_64", "BUFLEN_128", "BUFLEN_256"])
# PUBLIC_INTERFACE
def test_guarded_macro_preserves_caller_definition(compiler, name):
    """C-VARIANT: guarded compatibility macros must preserve caller values."""
    _assert_compiles(
        compiler, f'_Static_assert({name} == 777, "caller macro changed");\n',
        (f"-D{name}=777",),
    )


@pytest.mark.parametrize("body", [
    "void (*contract_probe)(CellularContextInitInputStruct *) = &cellular_hal_init;\n",
    "int (*contract_probe)(CellularProfileStruct *, int *) = &cellular_hal_get_profile_list;\n",
    "int (*contract_probe)(unsigned int *) = &cellular_hal_sim_power_enable;\n",
], ids=["wrong-return", "wrong-output-indirection", "wrong-parameters"])
# PUBLIC_INTERFACE
def test_incompatible_api_types_rejected(compiler, body):
    """C-API: the compiler must reject incompatible API use, not accept it."""
    result = _compile(compiler, body)
    assert result.returncode != 0, "Compiler unexpectedly accepted an incompatible API type"
    assert "incompatible" in result.stderr.lower(), result.stderr
