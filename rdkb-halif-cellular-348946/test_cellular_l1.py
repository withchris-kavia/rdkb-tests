"""Cellular L1 interface contracts; no runtime vendor HAL coverage is claimed."""

from pathlib import Path
import re
import shutil
import subprocess

import pytest

HEADER = (
    Path(__file__).resolve().parents[2]
    / "rdkb-halif-cellular-348946/include/cellular_hal.h"
)
# Independent type expectations are checked against the source, not extracted from it.
API_TYPES = {
    "cellular_hal_IsModemDevicePresent": "unsigned int (*)(void)",
    "cellular_hal_init": "int (*)(CellularContextInitInputStruct *)",
    "cellular_hal_open_device": "int (*)(CellularDeviceContextCBStruct *)",
    "cellular_hal_IsModemControlInterfaceOpened": "unsigned char (*)(void)",
    "cellular_hal_select_device_slot": "int (*)(cellular_device_slot_status_api_callback)",
    "cellular_hal_sim_power_enable": "int (*)(unsigned int, unsigned char)",
    "cellular_hal_get_total_no_of_uicc_slots": "int (*)(unsigned int *)",
    "cellular_hal_get_uicc_slot_info": "int (*)(unsigned int, CellularUICCSlotInfoStruct *)",
    "cellular_hal_get_active_card_status": "int (*)(CellularUICCStatus_t *)",
    "cellular_hal_monitor_device_registration": "int (*)(cellular_device_registration_status_callback)",
    "cellular_hal_profile_create": "int (*)(CellularProfileStruct *, cellular_device_profile_status_api_callback)",
    "cellular_hal_profile_delete": "int (*)(CellularProfileStruct *, cellular_device_profile_status_api_callback)",
    "cellular_hal_profile_modify": "int (*)(CellularProfileStruct *, cellular_device_profile_status_api_callback)",
    "cellular_hal_get_profile_list": "int (*)(CellularProfileStruct **, int *)",
    "cellular_hal_start_network": "int (*)(CellularNetworkIPType_t, CellularProfileStruct *, CellularNetworkCBStruct *)",
    "cellular_hal_stop_network": "int (*)(CellularNetworkIPType_t)",
    "cellular_hal_get_signal_info": "int (*)(CellularSignalInfoStruct *)",
    "cellular_hal_get_cell_location_info": "int (*)(CellLocationInfoStruct *)",
    "cellular_hal_set_modem_operating_configuration": "int (*)(CellularModemOperatingConfiguration_t)",
    "cellular_hal_get_device_imei": "int (*)(char *)",
    "cellular_hal_get_device_imei_sv": "int (*)(char *)",
    "cellular_hal_get_modem_current_iccid": "int (*)(char *)",
    "cellular_hal_get_modem_current_msisdn": "int (*)(char *)",
    "cellular_hal_get_packet_statistics": "int (*)(CellularPacketStatsStruct *)",
    "cellular_hal_get_current_modem_interface_status": "int (*)(CellularInterfaceStatus_t *)",
    "cellular_hal_set_modem_network_attach": "int (*)(void)",
    "cellular_hal_set_modem_network_detach": "int (*)(void)",
    "cellular_hal_get_modem_firmware_version": "int (*)(char *)",
    "cellular_hal_get_current_plmn_information": "int (*)(CellularCurrentPlmnInfoStruct *)",
    "cellular_hal_get_available_networks_information": "int (*)(CellularNetworkScanResultInfoStruct **, unsigned int *)",
    "cellular_hal_get_modem_preferred_radio_technology": "int (*)(char *)",
    "cellular_hal_set_modem_preferred_radio_technology": "int (*)(char *)",
    "cellular_hal_get_modem_current_radio_technology": "int (*)(char *)",
    "cellular_hal_get_modem_supported_radio_technology": "int (*)(char *)",
    "cellular_hal_modem_factory_reset": "int (*)(void)",
    "cellular_hal_modem_reset": "int (*)(void)",
}
CALLBACK_TYPES = {
    "cellular_device_open_status_api_callback": "int (*)(char *, char *, CellularDeviceOpenStatus_t, CellularModemOperatingConfiguration_t)",
    "cellular_device_removed_status_api_callback": "int (*)(char *, CellularDeviceDetectionStatus_t)",
    "cellular_device_slot_status_api_callback": "int (*)(char *, char *, int, CellularDeviceSlotStatus_t)",
    "cellular_device_registration_status_callback": "int (*)(CellularDeviceNASStatus_t, CellularDeviceNASRoamingStatus_t, CellularModemRegisteredServiceType_t)",
    "cellular_device_profile_status_api_callback": "int (*)(char *, CellularPDPType_t, CellularDeviceProfileSelectionStatus_t)",
    "cellular_network_packet_service_status_api_callback": "int (*)(char *, CellularNetworkIPType_t, CellularNetworkPacketStatus_t)",
    "cellular_device_network_ip_ready_api_callback": "int (*)(CellularIPStruct *, CellularDeviceIPReadyStatus_t)",
}
BUFFERS = [
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
# Enum sequences are independent published numeric-contract expectations.
ENUM_GROUPS = [
    (1, "IF_UP IF_DOWN IF_UNKNOWN IF_DORMANT IF_NOTPRESENT IF_LOWERLAYERDOWN IF_ERROR"),
    (1, "IP_FAMILY_UNKNOWN IP_FAMILY_IPV4 IP_FAMILY_IPV6 IP_FAMILY_IPV4_IPV6"),
    (1, "PREF_GPRS PREF_EDGE PREF_UMTS PREF_UMTSHSPA PREF_CDMA2000OneX PREF_CDMA2000HRPD PREF_LTE PREF_NR"),
    (0, "CELLULAR_PDP_TYPE_IPV4 CELLULAR_PDP_TYPE_PPP CELLULAR_PDP_TYPE_IPV6 CELLULAR_PDP_TYPE_IPV4_OR_IPV6"),
    (0, "CELLULAR_PDP_AUTHENTICATION_NONE CELLULAR_PDP_AUTHENTICATION_PAP CELLULAR_PDP_AUTHENTICATION_CHAP"),
    (0, "CELLULAR_PROFILE_TYPE_3GPP CELLULAR_PROFILE_TYPE_3GPP2"),
    (1, "CELLULAR_PDP_NETWORK_CONFIG_NAS CELLULAR_PDP_NETWORK_CONFIG_DHCP"),
    (1, "CELLULAR_MODEM_SET_ONLINE CELLULAR_MODEM_SET_OFFLINE CELLULAR_MODEM_SET_LOW_POWER_MODE CELLULAR_MODEM_SET_RESET CELLULAR_MODEM_SET_FACTORY_RESET"),
    (0, "CELLULAR_MODEM_REGISTERED_SERVICE_NONE CELLULAR_MODEM_REGISTERED_SERVICE_PS CELLULAR_MODEM_REGISTERED_SERVICE_CS CELLULAR_MODEM_REGISTERED_SERVICE_CS_PS"),
    (1, "DEVICE_REGISTERED DEVICE_NOT_REGISTERED"),
    (0, "CELLULAR_NETWORK_IP_FAMILY_UNKNOWN CELLULAR_NETWORK_IP_FAMILY_IPV4 CELLULAR_NETWORK_IP_FAMILY_IPV6 CELLULAR_NETWORK_IP_FAMILY_UNSPECIFIED"),
    (0, "CELLULAR_UICC_FORM_FACTOR_1FF CELLULAR_UICC_FORM_FACTOR_2FF CELLULAR_UICC_FORM_FACTOR_3FF CELLULAR_UICC_FORM_FACTOR_4FF"),
    (0, "CELLULAR_UICC_STATUS_VALID CELLULAR_UICC_STATUS_BLOCKED CELLULAR_UICC_STATUS_ERROR CELLULAR_UICC_STATUS_EMPTY"),
    (0, "CELLULAR_UICC_APPLICATION_USIM CELLULAR_UICC_APPLICATION_ISIM CELLULAR_UICC_APPLICATION_ESIM"),
    (1, "DEVICE_DETECTED DEVICE_REMOVED"),
    (1, "DEVICE_OPEN_STATUS_NOT_READY DEVICE_OPEN_STATUS_INPROGRESS DEVICE_OPEN_STATUS_READY"),
    (1, "DEVICE_SLOT_STATUS_NOT_READY DEVICE_SLOT_STATUS_SELECTING DEVICE_SLOT_STATUS_READY"),
    (1, "DEVICE_NAS_STATUS_NOT_REGISTERED DEVICE_NAS_STATUS_REGISTERING DEVICE_NAS_STATUS_REGISTERED"),
    (1, "DEVICE_NAS_STATUS_ROAMING_OFF DEVICE_NAS_STATUS_ROAMING_ON"),
    (1, "PROFILE_STATUS_INACTIVE PROFILE_STATUS_ACTIVE"),
    (1, "DEVICE_PROFILE_STATUS_NOT_READY DEVICE_PROFILE_STATUS_CONFIGURING DEVICE_PROFILE_STATUS_READY DEVICE_PROFILE_STATUS_DELETED"),
    (1, "DEVICE_NETWORK_IP_NOT_READY DEVICE_NETWORK_IP_READY"),
    (1, "DEVICE_NETWORK_STATUS_DISCONNECTED DEVICE_NETWORK_STATUS_CONNECTED"),
]


@pytest.fixture(params=(False, True), ids=("default", "lite"))
def lite(request):
    """Select each supported header feature mode without vendor dependencies."""
    return request.param


def _compile(source, lite):
    """Check real header contracts with bounded syntax-only C11 compilation."""
    compiler = shutil.which("cc")
    assert compiler, "Cellular contract checks require a C11 compiler named cc"
    flags = ["-DCELLULAR_MGR_LITE"] if lite else []
    result = subprocess.run(
        [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsyntax-only",
         "-I", str(HEADER.parent), *flags, "-x", "c", "-"],
        input='#include "cellular_hal.h"\n#include "cellular_hal.h"\n' + source,
        capture_output=True, text=True, timeout=20, cwd=HEADER.parent.parent,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# PUBLIC_INTERFACE
@pytest.mark.parametrize("api", API_TYPES)
def test_l1_public_api_type(api, lite):
    """Verify every public declaration independently in default and lite modes."""
    _compile(
        f'_Static_assert(_Generic(&{api}, {API_TYPES[api]}: 1, default: 0),'
        f' "{api} signature");', lite,
    )


# PUBLIC_INTERFACE
@pytest.mark.parametrize("callback", CALLBACK_TYPES)
def test_l1_callback_type(callback, lite):
    """Verify callback return and argument types without invoking callbacks."""
    _compile(
        f'_Static_assert(_Generic(({callback})0, {CALLBACK_TYPES[callback]}: 1,'
        f' default: 0), "{callback} signature");', lite,
    )


# PUBLIC_INTERFACE
@pytest.mark.parametrize(
    "structure,field,size", BUFFERS,
    ids=[f"{structure}.{field}" for structure, field, _ in BUFFERS],
)
def test_l1_character_array_contract(structure, field, size, lite):
    """Check fixed char-array element type and capacity, not runtime writes."""
    expression = f"(({structure} *)0)->{field}"
    _compile(
        f'_Static_assert(sizeof({expression}) == {size}, "{field} capacity");\n'
        f'_Static_assert(_Generic(&{expression}, char (*)[{size}]: 1, default: 0),'
        f' "{field} array type");', lite,
    )


# PUBLIC_INTERFACE
def test_l1_constants(lite):
    """Validate actual return, unknown-ID, handle, boolean and buffer constants."""
    values = {
        "RETURN_OK": 0, "RETURN_ERROR": -1, "TRUE": 1, "FALSE": 0,
        "BUFLEN_8": 8, "BUFLEN_32": 32, "BUFLEN_64": 64,
        "BUFLEN_128": 128, "BUFLEN_256": 256,
        "CELLULAR_PROFILE_ID_UNKNOWN": -1, "CELLULAR_SLOT_ID_UNKNOWN": -1,
        "CELLULAR_PDP_CONTEXT_UNKNOWN": -1,
        "CELLULAR_PACKET_DATA_INVALID_HANDLE": "0xFFFFFFFF",
    }
    _compile("\n".join(
        f'_Static_assert({name} == ({value}), "{name} value");'
        for name, value in values.items()
    ), lite)


# PUBLIC_INTERFACE
def test_l1_enum_values(lite):
    """Validate all 23 enum sequences without asserting vendor acceptance rules."""
    _compile("\n".join(
        f'_Static_assert({name} == {value}, "{name} enum value");'
        for first, symbols in ENUM_GROUPS
        for value, name in enumerate(symbols.split(), start=first)
    ), lite)


# PUBLIC_INTERFACE
def test_l1_qmi_feature_selection(lite):
    """Check that lite avoids QMI_SUPPORT while the default defines it."""
    condition = "ifdef" if lite else "ifndef"
    _compile(
        f"#{condition} QMI_SUPPORT\n#error unexpected QMI feature selection\n#endif\n",
        lite,
    )


# PUBLIC_INTERFACE
def test_l1_inventory_matches_header():
    """Detect inventory drift in this header's plain function declarations."""
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", HEADER.read_text(), flags=re.S)
    declarations = set(re.findall(
        r"^\s*(?:int|unsigned\s+int|unsigned\s+char)\s+"
        r"(cellular_hal_\w+)\s*\([^;]*\)\s*;",
        source, flags=re.M,
    ))
    assert declarations == set(API_TYPES), (
        f"Uninventoried: {declarations - set(API_TYPES)}; "
        f"removed: {set(API_TYPES) - declarations}"
    )
