# Bridge-util static contract test matrix

Authoritative inputs in `rdkb-halif-bridge-util-348946/include/`:
`bridge_util_hal.h` and `network_interface.h`.

| Requirement | Contract source | Pytest function |
|---|---|---|
| B-API | Seven public function declarations | test_api_signature |
| B-VALUE | Numeric macros and unconditional enum declarations | test_numeric_contract |
| B-BUFFER | bridgeDetails and Gateway_Config_Non_Ovs_Bridge arrays | test_structure_buffer_capacity |
| B-GLOBAL | Fifteen extern variable declarations | test_global_type, test_global_array_extent |
| B-FEATURE | WIFI_MANAGE_SUPPORTED, AMENITIES_NETWORK_ENABLED, _CBR2_PRODUCT_REQ_ conditionals | test_feature_views |
| B-INCLUDE | Both header guards and self-contained includes | test_header_repeat_inclusion |
| B-NEGATIVE | C type compatibility for declared functions and arrays | test_incompatible_types_rejected |

Each parameter case is listed in the Python module. Feature coverage evaluates
all eight combinations of the three boolean macros, checking the four gated
enumerators for presence/value or absence as appropriate. This is source feature
configuration coverage, not runtime branch coverage or target ABI verification.

Tests compile snippets against the real headers on stdin, without linking,
calling vendor functions, defining a fake HAL, or creating native test files.
GNU C11 is deliberate: bridge_util_log uses a GNU named variadic macro.
Compilation has a 20-second tooling timeout, unrelated to HAL timing guarantees.
No device, privileges, network, configuration schema, custom marker or cleanup of
device state is required. Each compiler process terminates before the next check.

## Gaps and limits

- `getVendorIfaces()` has an unspecified C parameter list. Its test preserves
  the actual declaration and does not claim enforcement of zero arguments.
- `updateBridgeInfo` documents enum OVS_CMD, absent from these two headers.
  No numeric operation range is invented.
- Header logging documentation says stdout is a fallback, but the macro has
  no stdout branch. Runtime logging behavior is not asserted by this suite.
- No runtime return codes, interface-list mutations, bridge configuration,
  vendor pre/post sequencing, target layouts or string termination are tested.
- No generated AST inventory or full declaration-set freshness gate is claimed.
- These tests provide static checks of all seven declared function signatures;
  they are not runtime L1/L2/L3 acceptance and not implementation line/branch
  coverage. No production sources are changed.

Run from the workspace root:

    python -m pytest rdkb-tests/rdkb-halif-bridge-util-348946/ --collect-only -q
    python -m pytest rdkb-tests/rdkb-halif-bridge-util-348946/ -q

Prerequisites: Python 3.10+, pytest, GNU-compatible `cc` with standard POSIX
development headers. Source and test repositories must remain sibling folders.
Results are recorded in the central README after validation.
