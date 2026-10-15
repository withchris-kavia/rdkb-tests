# rdkb-tests

## rdkb-halif-cellular-348946

### L1 cellular interface-contract suite

Test: [test_cellular_l1.py](rdkb-halif-cellular-348946/test_cellular_l1.py).
Source repository: `rdkb-halif-cellular-348946` (not the cellular-modem repository).
Prerequisites: Python 3, pytest, and a C11 compiler named `cc`.

| Test name | Coverage |
| --- | --- |
| `test_l1_public_api_type` | All 36 public function types in default and lite modes: 72 cases. |
| `test_l1_callback_type` | Seven callback typedef signatures in both modes: 14 cases. |
| `test_l1_character_array_contract` | Seventeen fixed character-array types/capacities in both modes: 34 cases. |
| `test_l1_constants` | Status, boolean, buffer-size, unknown-ID and invalid-handle constants: two cases. |
| `test_l1_enum_values` | All 23 enum sequences in both modes: two cases. |
| `test_l1_qmi_feature_selection` | Default QMI_SUPPORT and lite feature behavior: two cases. |
| `test_l1_inventory_matches_header` | Detect added/removed public declarations: one case. |

Working directory: workspace root. No network, vendor library, or modem access:

```sh
python -m pytest rdkb-tests/rdkb-halif-cellular-348946/test_cellular_l1.py --collect-only -q
python -m pytest rdkb-tests/rdkb-halif-cellular-348946/test_cellular_l1.py -q
```

Expected example — not an observed run: 127 contract cases pass with exit 0.
Changed signatures, constants, array capacities, enums, feature selection, or
inventory fail with exit 1. Missing compiler/header prerequisites fail rather
than being silently counted as passes. Collection errors establish no coverage.

These checks provide header-contract coverage only. Runtime success, rejection,
buffer boundaries, callback behavior, and injected dependency failures remain
blocked by missing real implementation, isolation support, and a supported
Python interface. NULL profiles are valid default selection for create/start;
do not blanket-test them as invalid. The RETURN_ERR/RETURN_ERROR documentation
mismatch and other ambiguities are recorded in the
[per-API checkpoint](rdkb-halif-cellular-348946/hal_l1_progress.md).
Observed verification: **127 collected, 127 passed** in 15.25 seconds,
successful status 0; no failures or skips. Inventory totals were independently
validated and header/test SHA-256 identities are recorded in the checkpoint.
This is contract verification, not runtime HAL line/branch coverage.
No reset, factory reset, network attach, or SIM operation is invoked.

## rdkb-halif-cellular-modem-348946

### L1 CellularModem

The `[L1 CellularModem]` suite is stored in [test_cellular_modem_l1.c](rdkb-halif-cellular-modem-348946/test_cellular_modem_l1.c). Its source repository is `rdkb-halif-cellular-modem-348946`.

The suite registers one L1 runtime test, `Modem_Firmware_Version_negative_null_buffer`, which calls `Modem_Firmware_Version(NULL)` and expects `STATUS_FAILED`. This expectation follows the interface requirement for an output buffer of at least 128 bytes and its documented failure result for invalid parameters. The test does not assert output preservation on failure.

The source also contains C11 compile-time checks for the declarations of `Modem_FactoryReset`, `Modem_Reboot`, and `Modem_Firmware_Version`, and for the values of `STATUS_SUCCESS` and `STATUS_FAILED`. These are declaration checks, not runtime behavioral tests. Suite and test registration failures are checked.

### Prerequisites and missing dependencies

Building requires a C11-capable compiler, ut-core headers and libraries with its compatible CUnit variant, and a cellular-modem HAL implementation whose hardware dependencies are isolated through a lower-level shim or stubs. The interface header is available at [cellular_modem_hal_api.h](../rdkb-halif-cellular-modem-348946/include/cellular_modem_hal_api.h), but declarations alone cannot supply the implementation under test.

The reported verification found no local ut-core framework, HAL implementation, or hardware-isolation shim. Compilation and execution were therefore not performed. Do not substitute a preset-return mock of the public HAL function and interpret its result as implementation coverage. Execution must wait until the real implementation can be tested safely without modem hardware access.

The source repository's [build_ut.sh](../rdkb-halif-cellular-modem-348946/build_ut.sh) clones a companion test repository and delegates to its build script. It does not explicitly integrate this centrally stored source, so it is not a verified build command for this suite.

### Conditional build and execution instructions

Use the workspace root as the working directory. Once the missing dependencies are supplied, set `UT_CORE_CPPFLAGS` to the framework include/compiler flags, `UT_CORE_LDFLAGS` to its compatible framework and CUnit link flags, and `ISOLATED_CELLULAR_MODEM_LDFLAGS` to the isolated HAL implementation and its dependency link flags. These are command inputs defined here, not existing workspace configuration. Their values must be supplied by the dependency owner; no library names or installation paths have been verified.

The following non-interactive build command requires those inputs and produces the binary in the existing repository-named test directory. It is conditional guidance, not a verified build recipe.

```sh
cc -std=c11 \
  -Irdkb-halif-cellular-modem-348946/include \
  ${UT_CORE_CPPFLAGS:?Supply ut-core and compatible CUnit compiler flags} \
  rdkb-tests/rdkb-halif-cellular-modem-348946/test_cellular_modem_l1.c \
  ${ISOLATED_CELLULAR_MODEM_LDFLAGS:?Supply isolated HAL implementation link flags} \
  ${UT_CORE_LDFLAGS:?Supply ut-core and compatible CUnit link flags} \
  -o rdkb-tests/rdkb-halif-cellular-modem-348946/test_cellular_modem_l1
```

After a successful build, run the binary from the same workspace-root working directory in basic mode. Do not use interactive console mode.

```sh
./rdkb-tests/rdkb-halif-cellular-modem-348946/test_cellular_modem_l1 -b
```

### Possible output and exit status

Expected example — not an observed run: if the isolated implementation returns `STATUS_FAILED` for the null buffer and framework initialization, registration, and execution succeed without assertion failures, the binary returns `EXIT_SUCCESS` (zero). Exact framework output is not known.

Expected example — not an observed run: if the returned value differs from `STATUS_FAILED`, the assertion fails and the binary returns `EXIT_FAILURE`. The binary also returns `EXIT_FAILURE` when framework initialization, registration, or execution reports failure. Missing headers, libraries, or implementation symbols prevent building; these are prerequisite failures, not observed test assertion failures.

### Verification status and coverage limitations

The test source was reported approved and materialized. Documentation inspection confirmed that the linked source exists and contains the named L1 test, compile-time checks, and checked registration. No compilation or execution was performed, and there is no observed pass result or measured coverage.

Factory reset and reboot have no runtime tests and are never invoked by this suite. Firmware-version success, minimum-buffer behavior, and lower-level retrieval-error injection are not tested. Further behavioral coverage remains blocked by missing implementation dependencies, including a deterministic firmware fixture and a hardware-isolation shim. The single created negative test does not establish complete per-API or four-axis coverage.

### L2 cellular-modem firmware integration suite

The L2-only pytest suite is stored in [test_cellular_modem_l2.py](rdkb-halif-cellular-modem-348946/test_cellular_modem_l2.py). Its source repository is `rdkb-halif-cellular-modem-348946`. It invokes the real vendor shared-library ABI through `ctypes` in bounded child processes; it does not mock or implement the HAL.

The suite contains the following three pytest cases. The identifiers below are relative to the test module.

| Test identifier | Purpose and assertions |
| --- | --- |
| `test_l2_firmware_matches_lab_reference[minimum_buffer]` | Calls `Modem_Firmware_Version` with the documented minimum 128-byte buffer and checks success status, NUL termination, an exact UTF-8 firmware match against an independent lab reference, and intact 16-byte guards before and after the buffer. |
| `test_l2_firmware_matches_lab_reference[larger_buffer]` | Applies the same checks with a 256-byte caller buffer. |
| `test_l2_sequential_firmware_reads_are_consistent` | Performs two serial reads in one HAL child process with a 128-byte buffer, applies the same checks to each result, and checks that the firmware remains consistent. |

### L2 prerequisites and runtime configuration

Execution requires Python 3.9 or newer because the probe parser uses `str.removeprefix`, pytest, a compatible vendor build of `libhal_cellular_modem_hal_api.so` with its native dependencies available to the loader, and a ready lab modem accessible to that build. The interface header alone is not an implementation. No verified vendor build or installation command is supplied by this suite; obtain the compatible binary and device setup from the vendor or lab owner. Do not use a preset-return mock as the implementation under test.

Request the following exact environment-variable names through the supported runtime environment mechanism. The suite does not read or write `.env`, and no actual library path or firmware value is prescribed here.

| Environment variable | Requirement and purpose |
| --- | --- |
| `CELLULAR_MODEM_L2_ENABLED` | Required for hardware execution. Only the exact value `1` explicitly authorizes read-only lab-device access. Any other value, including an unset variable, skips all cases before validating the remaining configuration. |
| `CELLULAR_MODEM_HAL_LIBRARY` | Required after opt-in. Supplies an existing absolute path to the compatible vendor shared library exporting `Modem_Firmware_Version`. |
| `CELLULAR_MODEM_EXPECTED_FIRMWARE` | Required after opt-in. Supplies the independently verified lab firmware string. It must be nonempty, contain no NUL character, and encode to fewer than 128 UTF-8 bytes so it fits the minimum ABI buffer with a terminator. |
| `CELLULAR_MODEM_L2_TIMEOUT_SECONDS` | Optional. Sets the subprocess harness deadline in seconds, defaulting to `30`. The value must be numeric, finite, and strictly positive. This is a harness deadline, not a modem configuration setting. |

Run serially against a given modem; the module warns that thread safety is not promised. Factory reset and reboot are intentionally excluded because safe recovery and independent state observation are not established for those operations.

### L2 setup and execution

Use the workspace root as the working directory. If pytest is absent, install it non-interactively into the intended Python environment:

```sh
python -m pip install --disable-pip-version-check --no-input pytest
```

Collect the suite and check its safe default behavior without authorizing device access:

```sh
python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/test_cellular_modem_l2.py --collect-only -q
env -u CELLULAR_MODEM_L2_ENABLED python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/test_cellular_modem_l2.py -q -rs
```

After the lab owner supplies the library path and independently verified firmware through the supported environment mechanism and authorizes access with `CELLULAR_MODEM_L2_ENABLED=1`, run the configured suite:

```sh
python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/test_cellular_modem_l2.py -q -rs
```

To target one case from the same workspace-root working directory, use its full node identifier:

```sh
python -m pytest 'rdkb-tests/rdkb-halif-cellular-modem-348946/test_cellular_modem_l2.py::test_l2_firmware_matches_lab_reference[minimum_buffer]' -q -rs
```

### L2 possible output and exit status

Expected example — not an observed run: with valid lab configuration and matching HAL results, the three cases pass and pytest exits `0`. Incorrect status, firmware mismatch, missing termination, modified guard bytes, a native probe failure, or expiration of the harness deadline produces failures and exit code `1`. Invalid required configuration after opt-in produces fixture errors rather than successful behavioral checks.

Without opt-in, pytest reports skipped cases with the reason `L2 lab-device access requires CELLULAR_MODEM_L2_ENABLED=1`. An all-skipped run can exit `0`, but it is not behavioral verification. Pytest exit codes `2`, `3`, `4`, and `5` respectively mean interruption, internal error, usage error, and no tests collected.

### L2 verification status and coverage limitations

Focused verification from the `rdkb-tests` working directory collected all three cases successfully. A subsequent run with `CELLULAR_MODEM_L2_ENABLED` explicitly unset reported `3 skipped`; both commands completed successfully with exit code `0`. The observed collection identifiers matched the three cases listed above. The equivalent workspace-root commands are documented in the preceding section.

No real vendor library or lab modem was exercised during this verification. Real firmware retrieval, buffer boundaries, and sequential consistency remain unverified until configured hardware execution. This suite does not cover factory reset, reboot, invalid-pointer behavior, or injected lower-level retrieval failures. Existing L1 test files and documentation were left unchanged.

## rdkb-halif-bridge-util-348946

Source repository: `rdkb-halif-bridge-util-348946`. All new tests are Python
compatible with pytest and reside in the repository-named subfolder.

### Supplemental L1 header-contract suite

Module: [test_bridge_util_l1_contract.py](rdkb-halif-bridge-util-348946/test_bridge_util_l1_contract.py).
Prerequisites: Python 3, pytest, and a GNU-compatible C11 compiler named `cc`.
This module uses actual headers; no vendor API is linked, mocked, or invoked.

| Test name | Scope |
| --- | --- |
| `test_l1_api_types_across_feature_configurations` | Eight configurations, each checking all seven public API types using C11 generic selections. |
| `test_l1_conditional_symbol_visibility` | Four conditional enum symbols across eight configurations (32 cases); enabled symbols compile, disabled symbols must fail compilation after a successful control probe. |
| `test_l1_external_global_types_and_capacities` | One case checking public scalar/pointer globals and all four exported character-array types/capacities. |

Working directory: workspace root. Run without hardware or network access:

```sh
python -m pytest rdkb-tests/rdkb-halif-bridge-util-348946/test_bridge_util_l1_contract.py --collect-only -q
python -m pytest rdkb-tests/rdkb-halif-bridge-util-348946/test_bridge_util_l1_contract.py -q
```

Expected example — not an observed run: 41 contract cases pass with exit 0.
Changed API/global types or incorrect conditional visibility fail with exit 1.
Compiler/header prerequisites are checked, not skipped as passing coverage.
These are contract checks, not behavioral negative/boundary/error-return tests.
The C declaration `getVendorIfaces()` does not establish a strict no-argument
prototype. No runtime behavior is inferred from its compatible pointer type.
Behavioral L1 coverage remains blocked by absent implementation and isolation
support; see [coverage checkpoint](rdkb-halif-bridge-util-348946/hal_l1_progress.md).
Observed verification: all 41 new cases collected. Combined execution of this
module and the existing L1 module reported **64 passed**, exit 0 (41 new plus
23 existing contract checks; no failures or skips). No vendor HAL was exercised.
Commands and per-API behavioral gaps are recorded in the checkpoint.

### L1 interface-conformance suite

Module: [test_bridge_util_l1.py](rdkb-halif-bridge-util-348946/test_bridge_util_l1.py).
Prerequisites: Python 3, pytest, and a GNU-compatible C11 compiler named `cc`.
Compiler probes use the real source headers, not copied or fabricated HAL code.

| Test name | Cases and assertions |
| --- | --- |
| `test_l1_public_api_signature[api]` | Seven APIs: `updateBridgeInfo`, `checkIfExists`, `removeIfaceFromList`, `checkIfExistsInBridge`, `HandlePreConfigVendor`, `HandlePostConfigVendor`, `getVendorIfaces`; checks declaration compatibility. |
| `test_l1_bridge_buffer_capacity[field-size]` | Seven fields: `bridgeName`, `vlan_name`, `VirtualParentIfname`, `ethIfList`, `MoCAIfList`, `GreIfList`, `WiFiIfList`; checks buffer capacities. |
| `test_l1_network_contract` | Checks network-header include guards, buffer capacities, enums, and interface result constants. |
| `test_l1_feature_configuration[wifi-amenities-cbr2]` | Eight boolean feature combinations; checks base and enabled conditional configuration values. |

These 23 checks provide declaration/data-contract coverage only, not runtime
HAL unit coverage. For each of the seven APIs, positive, invalid-input,
boundary, and injected dependency-failure runtime coverage remains unavailable:
there is no local vendor implementation or lower-level shim. Null-input rules
are unspecified. `removeIfaceFromList` has no error return; `getVendorIfaces`
returns a string pointer or NULL. The referenced `OVS_CMD` enum is absent from
both local headers, so no operation values are invented.

### L2 opt-in vendor integration suite

Module: [test_bridge_util_l2.py](rdkb-halif-bridge-util-348946/test_bridge_util_l2.py).
Prerequisites: Python 3, pytest, a compatible real vendor shared library with
its native dependencies, and independently verified stable lab topology.
Run serially because thread safety is not promised.

| Test name | Cases and assertions |
| --- | --- |
| `test_l2_remove_interface_from_list[middle/first/last/only/empty/absent]` | Six cases verify removal content/order and exact no-op behavior when absent. |
| `test_l2_interface_existence[existing/absent]` | Two cases verify 0/-1 against independent interface-presence references. |
| `test_l2_bridge_membership[member/nonmember]` | Two cases verify 0/-1 against independent bridge-membership references. |

Request the following variables through the supported runtime environment
mechanism; the tests never read or write `.env`:

- `BRIDGE_UTIL_L2_ENABLED`: exact value `1` explicitly authorizes lab access.
  Otherwise all L2 cases skip before library loading.
- `BRIDGE_UTIL_HAL_LIBRARY`: existing absolute vendor-library path. The source
  specification names both `libhalbridge_utils.so` and `libbridge_utils.so`;
  obtain the compatible actual binary from the vendor.
- `BRIDGE_UTIL_EXISTING_IFACE` / `BRIDGE_UTIL_ABSENT_IFACE`: independently
  confirmed present/absent interfaces.
- `BRIDGE_UTIL_BRIDGE`: existing lab bridge.
- `BRIDGE_UTIL_MEMBER_IFACE` / `BRIDGE_UTIL_NONMEMBER_IFACE`: independently
  confirmed member/nonmember interfaces for that bridge.

Interface and bridge names must be nonempty ASCII, shorter than 16 bytes,
without whitespace. Each native probe runs in a child process with a
30-second deadline. No bridge mutation, pre/post vendor configuration, reset,
or invalid-pointer call is performed. Runtime `getVendorIfaces` coverage is
absent because pointer ownership/lifetime and bounded length are unspecified.
No injected dependency-failure coverage is claimed.

### Execution and possible output

Working directory: workspace root (`code-generation`). Pytest discovers these
modules directly; no application-entrypoint or production changes are required.

```sh
python -m pytest rdkb-tests/rdkb-halif-bridge-util-348946/ --collect-only -q
env -u BRIDGE_UTIL_L2_ENABLED python -m pytest rdkb-tests/rdkb-halif-bridge-util-348946/ -q -rs
```

After the lab owner supplies all relevant variables and authorizes access:

```sh
python -m pytest rdkb-tests/rdkb-halif-bridge-util-348946/test_bridge_util_l2.py -q -rs
```

Observed same-turn verification: collection reported **33 tests collected**.
The safe-default run reported **23 passed, 10 skipped**, exit code 0.
Every L2 skip reported `L2 lab access requires BRIDGE_UTIL_L2_ENABLED=1`.
No real vendor library or lab network was exercised.

Expected example — not an observed vendor run: correctly configured L2 cases
pass when native results match independent topology references. Changed header
contracts, incorrect native results, native crashes, or timeouts fail (exit 1).
Invalid opted-in configuration causes errors, not passes. Exit 0 does not make
skipped cases behavioral verification. Pytest exits 2/3/4/5 mean
interruption/internal error/usage error/no tests collected.

## code-generation

### HAL L1 skill orchestration regression suite

Source root: `code-generation` (the workspace-owned skill, not a HAL repository).
Test: [test_hal_l1_orchestration.py](code-generation/test_hal_l1_orchestration.py).
The Python tests exercise the actual Python 3 runner in
`skills/rdkb_hal_l1_suite_builder/scripts/run_suite.py`; they do not convert or
replace native HAL unit tests and establish no HAL behavioral coverage.

Test names:
- `test_success_and_resume`: fresh passing evidence, preserved coverage gaps, new run IDs.
- `test_stale_results_not_reused`: old JUnit results cannot establish a current pass.
- `test_nonpassing_evidence`: failure, error, and skip statuses are not passes.
- `test_invalid_evidence`: malformed, empty, and duplicate JUnit case evidence.
- `test_invalid_configuration`: path escapes, missing support, invalid timeout and argv.
- `test_header_change_rejects_resume`: changed headers invalidate resume compatibility.
- `test_build_failure_stops_run`: nonzero build exit retains diagnostics and stops execution.
- `test_nonzero_run_preserves_case_evidence`: native assertion exits retain per-case XML.
- `test_execution_boundaries`: timeout, interruption, and missing executable checkpoints.

Prerequisites: Python 3.9+ and pytest; no native HAL dependencies, hardware or network.
Working directory: workspace root. Run:

```sh
python3 -m pytest rdkb-tests/code-generation/test_hal_l1_orchestration.py -q
python3 skills/rdkb_hal_l1_suite_builder/scripts/run_suite.py --help
```

Expected example — not an observed run: all selected cases pass with pytest exit
0; assertion failures exit 1. Collection/import failures are not successful
verification. Real native UT execution remains conditional on a locally available
implementation, existing framework, shim/stubs and fresh JUnit exporter.
