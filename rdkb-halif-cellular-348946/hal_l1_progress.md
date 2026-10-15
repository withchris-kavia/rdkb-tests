# Cellular HAL L1 coverage checkpoint

Repository: `rdkb-halif-cellular-348946`.
Capability: header/specification only; no implementation, Python binding,
local native UT directory, or lower-level isolation support found.
Framework: pytest; compiler: `cc -std=c11 -Wall -Wextra -Werror -fsyntax-only`.
Header: `include/cellular_hal.h`. Specification: `docs/pages/CellularHalSpec.md`.
Configurations: default and `CELLULAR_MGR_LITE`; only default defines QMI_SUPPORT.
`build_ut.sh` clones a companion suite and does not integrate these central tests.

## Inventory and contract mapping

Exact independent API pointer signatures appear in `API_TYPES` in
[test_cellular_l1.py](test_cellular_l1.py). These 36 entries are checked against
source declarations by an inventory-parity test and two compiler cases per API.
Seven callback signatures are separately checked and not counted as public APIs.

The following table uses the `cellular_hal_` prefix for every API.
All runtime axes lack implementation support. `U` means SPEC_UNCLEAR;
`B` means BLOCKED by implementation/isolation support; `N/A` means no applicable
input/parameter boundary. B/U keeps both a known obligation and unclear details.

| API suffix | Return type | Positive | Negative | Boundary | Error-return | Contract notes |
| --- | --- | --- | --- | --- | --- | --- |
| IsModemDevicePresent | unsigned int | B | N/A | N/A | U | TRUE/FALSE availability; failure semantics absent |
| init | int | B | U | B/U | B/U | Context/profile enums; no NULL rule |
| open_device | int | B | U | U | B/U | Open/remove callbacks; missing callback NULL policy |
| IsModemControlInterfaceOpened | unsigned char | B | N/A | N/A | U | TRUE/FALSE state; failure semantics absent |
| select_device_slot | int | B | U | B/U | B/U | Slot callback; names at least 64 bytes; vendor slot numbers |
| sim_power_enable | int | B | U | B/U | B/U | Slot IDs depend on vendor slot count |
| get_total_no_of_uicc_slots | int | B | U | B/U | B/U | Vendor slot count 1 or 2 |
| get_uicc_slot_info | int | B | U | B/U | B/U | Unsigned index bound does not establish valid physical slots |
| get_active_card_status | int | B | U | B | B/U | UICC status enum |
| monitor_device_registration | int | B | U | B/U | B/U | Registration callback/state transitions |
| profile_create | int | B | U | B | B/U | NULL profile selects default, not invalid-input rejection |
| profile_delete | int | B | U | B/U | B/U | Profile/callback; NULL semantics unspecified |
| profile_modify | int | B | B/U | B/U | B/U | NULL profile explicitly returns error; numeric code unclear |
| get_profile_list | int | B | U | B/U | B/U | Count 0..2^31-1; returned-list ownership unclear |
| start_network | int | B | U | B | B/U | NULL profile uses default; packet/IP callbacks |
| stop_network | int | B | U | B | B/U | IP request enum |
| get_signal_info | int | B | U | B/U | B/U | RSSI, RSRQ, RSRP, SNR, TXPower; RSRQ fraction/int mismatch |
| get_cell_location_info | int | B | U | B/U | B/U | Documented 36-bit IDs vs unsigned-int storage |
| set_modem_operating_configuration | int | B | U | B | B/U | Includes reset/factory reset; isolation required |
| get_device_imei | int | B | U | B/U | B/U | Minimum buffer 16; formatted example exceeds capacity |
| get_device_imei_sv | int | B | U | B | B/U | Minimum buffer 16 |
| get_modem_current_iccid | int | B | U | B/U | B/U | Getter minimum 21 vs slot-info field 20 |
| get_modem_current_msisdn | int | B | U | B | B/U | Minimum buffer 20 |
| get_packet_statistics | int | B | U | B/U | B/U | Unsigned-long counters; overflow semantics unspecified |
| get_current_modem_interface_status | int | B | U | B | B/U | Interface-status enum |
| set_modem_network_attach | int | B | N/A | N/A | B/U | No input parameters; controlled state changes needed |
| set_modem_network_detach | int | B | N/A | N/A | B/U | No input parameters; controlled state changes needed |
| get_modem_firmware_version | int | B | U | B | B/U | Minimum buffer 128 |
| get_current_plmn_information | int | B | U | B/U | B/U | MCC/MNC 0..999; PLMN/status fields |
| get_available_networks_information | int | B | U | B/U | B/U | Count 0..1100000; returned-list ownership unclear |
| get_modem_preferred_radio_technology | int | B | U | B | B/U | Minimum buffer 128 |
| set_modem_preferred_radio_technology | int | B | U | B | B/U | Unsupported RAT defaults to AUTO, not necessarily rejection |
| get_modem_current_radio_technology | int | B | U | B | B/U | Minimum buffer 128 |
| get_modem_supported_radio_technology | int | B | U | B | B/U | Minimum buffer 128 |
| modem_factory_reset | int | B | N/A | N/A | B/U | Destructive unless isolated |
| modem_reset | int | B | N/A | N/A | B/U | Destructive unless isolated |

Documentation uses RETURN_ERR, but the header defines RETURN_ERROR (-1).
Do not silently assert the former equals the latter as a runtime requirement.
The specification denies asynchronous notifications while callback APIs exist:
clarify callback delivery/ordering before writing event assertions.
Do not treat TODOs or examples as complete input-rejection contracts.
Do not test undersized buffers through getters without a length argument.

## Feasible checks created

- API types: 36 APIs x 2 modes = 72 cases.
- Callback types: 7 callbacks x 2 modes = 14 cases.
- Fixed character arrays: 17 fields x 2 modes = 34 cases.
- Constants, enum sequences, and QMI feature selection: 6 cases.
- Source inventory parity: 1 case.
- Total planned: 127 contract cases, no behavioral cases.

Assertions use the real header and unevaluated C expressions. Compilation
does not link or execute modem code. No fake API implementation is supplied.

## Verification

Executed from the workspace root:

```sh
python -m pytest rdkb-tests/rdkb-halif-cellular-348946/test_cellular_l1.py --collect-only -q
python -m pytest rdkb-tests/rdkb-halif-cellular-348946/test_cellular_l1.py -q
```

Observed: 127 tests collected; 127 passed in 15.25 seconds, successful shell
status 0. Zero failures, skips, or not-run cases in the selected suite.
Every API has two passing declaration-type checks, not behavioral passes.
Independent inventory verification confirmed 36/7/17/23 APIs/callbacks/arrays/enums.
No modem, vendor library, or hardware/network operation was executed.

SHA-256 identities for this verified state:
- `cellular_hal.h`: `765547ec19ec80858176c2cda03013155a3bd7f4cadb7d92a0dc544cb9e60d28`
- `test_cellular_l1.py`: `5638b5d5023cfd58c3ce8ea04092db7d36f4eac08eb37a0242addee6eb1d793e`

## Coverage metrics

APIs inventoried: 36. Behavioral cases written/executed/passing: 0/0/0.
Contract cases written/collected/executed/passing: 127/127/127/127.
Contract pass rate: 100%; API declaration checks cover 36/36 in both modes.
APIs with behavioral passes: 0/36. Fully behaviorally covered APIs: 0/36.
Behavioral axis coverage: 0/132 (144 cells minus 12 justified N/A cells for
six no-argument functions' input and parameter-boundary axes).
Behavioral pass rate: N/A. Implementation line/branch coverage: not measured.
Documented return outcomes: 34 int APIs with success/error labels, plus two
boolean-result APIs = 72 API/outcome identities, 0 behaviorally covered.
Numeric error-code reconciliation is unresolved; dependency failure scenarios
will be enumerated after implementation discovery, not invented from this total.

## Resume

Next: obtain actual implementation, verified lower-level isolation, and supported
Python binding/executable interface. Implement profile default/modify-NULL behavior,
controlled output getters, and event/state transitions before destructive operations.
Resolve error symbols, list ownership, precision/range mismatches, and event delivery.
Check current header and test identity against this checkpoint before resuming;
invalidate and rerun affected evidence after source/fixture changes.
