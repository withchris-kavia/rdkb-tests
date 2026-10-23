# Cellular-modem HAL tests, traceability and workflow blockers

## Selected source and completed scope

Source repository: `rdkb-halif-cellular-modem-348946`.
Contract read: `include/cellular_modem_hal_api.h`.
Specification read: `docs/pages/CellularModemHalSpec.md`.
Paths above are relative to the source repository; test commands run from the
workspace root.

The header declares exactly these three public functions:

| API | Return | Parameters | Runtime scope considered |
|---|---|---|---|
| Modem_FactoryReset | int | void | Success/failure and erased configuration; destructive, requires approval and recoverable baseline |
| Modem_Reboot | int | void | Success/failure and actual restart; disruptive, requires approval, independent recovery and readiness evidence |
| Modem_Firmware_Version | int | char * | Output buffer minimum 128 bytes, success/failure, invalid parameter/retrieval failures |

This is a manually reviewed list, not an accepted AST-generated inventory.
No generated manifest, case IDs from an absent registry, or freshness gate is
claimed. The local requirement labels below are only static-test traceability,
not replacements for the requested manifest identity scheme.

## Executable static regression matrix

| Local requirement | Published source | Tests | Parameter cases | Expected result |
|---|---|---|---|---|
| M-API | Header's three function declarations | test_public_api_signature | Three APIs in C11 and C++11 | Exact typed pointer assignment compiles |
| M-API | C/C++ type compatibility for published declarations | test_incompatible_declaration_rejected | Wrong return, wrong firmware pointer depth, wrong reset parameters in both languages | Compilation fails with an error diagnostic |
| M-STATUS | Header STATUS_SUCCESS and STATUS_FAILED | test_status_constant | 0 and -1 in both languages | Compile-time equality assertion |
| M-INCLUDE | Header include guard and self-contained declarations | test_header_is_self_contained_and_repeatable | C11 and C++11 | Repeated inclusion compiles |
| M-LINKAGE | Header __cplusplus / extern "C" block | test_cpp_declarations_have_c_linkage | All APIs in one C++11 translation unit | Explicit C-linkage redeclarations compile |

Total: 19 static cases. A bounded compiler subprocess receives snippets on stdin
with `-fsyntax-only`; no C/C++ test case files, fake implementations, or HAL
binaries are created. All tests and assertions are Python/pytest. No hardware,
network, device mutation, secret, custom marker or configuration schema is used.
The 20-second timeout bounds compilation only, not HAL response time.

## Requested skill disposition

| Requested skill | Applied decision | Completion limitation |
|---|---|---|
| hal_contract_inventory | Read entrypoint; attempted required artifact-contract reference; checked required project inputs and parser infrastructure | FAILED_PREFLIGHT: required reference and inputs absent; no guessed manifests or regex parser |
| json_hal_client | Reviewed applicability and mandatory transport/schema inputs | Not applicable to the published C-only modem contract; no authorized JSON schema, server or library inputs supplied |
| native_c_hal_access | Checked native access prerequisites; retained all three APIs as runtime obligations | Blocked before wrapper generation: no manifest, parse view, environment/ABI/toolchain facts or shared core |
| pytest_component_test_author | Used authoritative-source review, API consideration, explicit gaps, pytest and traceability | Static contract checks authored/executed separately from runtime L1 acceptance |
| pytest_l2_test_author | Reviewed sequence/lifecycle obligations and required gate/interface inputs | Blocked: no L2 records/gate, native sequence interface, registry, evidence format or isolation/recovery facts |
| pytest_l3_test_author | Reviewed external-stimulus eligibility and proof/recovery requirements | Blocked: no bench/capabilities, stimulus drivers, normative external-action/observable mapping or authorization |

The shared Python pytest and test-storage skills also govern central placement
and the catalog update. No reusable skill package was modified.

## Exact missing inputs and owner actions

The workspace-wide prerequisite search found no `environment_info.md`,
`technical_spec.md`, `c_header_parser.py`, `json_schema_parser.py`,
`api_manifest.json`, `state_machines.json`, or `l2_requirements.json`.
No `tools/`, `harness/`, or `vts-test-generation-output/` implementation tree
was found at the workspace root during preflight.

1. Skill maintainer: restore the missing package file
   `skills/hal_contract_inventory/references/artifact_contract.md`.
   Its absent content cannot safely be reconstructed from the skill summary.
2. Project owner: supply the authoritative `environment_info.md` and
   `technical_spec.md` at their intended project paths. These must resolve
   contract include order, ABI, feature views, output layout, toolchain,
   deployment/serial and supported DUT availability.
3. Tooling owner: supply the single shared libclang-based
   `tools/contract_parser/c_header_parser.py` and JSON parser infrastructure,
   dependency declarations, documented invocation and tests. The whole
   `tools/contract_parser/` directory is absent; the parser's exact eventual
   location/interface must be confirmed rather than assumed.
4. Contract owner: supply the selected modem view under
   `tools/contract_parser/views/` (directory absent; exact HAL filename must be
   resolved from authoritative project configuration). Generate accepted
   `manifests/api_manifest.json`, `case_table.json`, `state_machines.json` and
   their collection freshness gate using that tooling, not this static suite.
5. Native tooling/bench owner: supply `tools/cli_common/`, actual native access
   interfaces, target toolchain file, exact vendor-library/ABI/export evidence,
   serial/DUT-pull access and safe lifecycle/adapter/recovery facts.
6. L2 owner: supply the selected `l2_requirements.json`, committed case schemas,
   classification registry, four-group evidence schema, supported-DUT matrix,
   service stop/restore matrix, authorization policy and persistent sequence
   fixtures. Their intended exact paths are not defined by available inputs.
7. L3 owner: supply the actual bench descriptor/capabilities and
   `harness/stimulus/` drivers, with independent external-action proof,
   contract-backed HAL observables, deadlines and verified restoration.
8. If a separate JSON interface is intended, its owner must explicitly select
   its schema and provide real server/config/library/toolchain facts. Do not
   map these three C APIs to an invented JSON protocol.

`FAILED_PREFLIGHT` above describes the skill workflow status, not a fabricated
registration in an absent outcome registry or a passing/skipped pytest case.
No blocked runtime cases are included in the static passing count.

## Runtime cases retained as blocked obligations

- L1: valid firmware retrieval with caller buffers of 128 bytes and larger;
  verify raw return status and output against the real vendor contract. The
  header does not define a maximum capacity, exact version format/length,
  termination guarantee, specific invalid-pointer semantics, or granular error
  mapping. Do not invoke NULL or undersized buffers based on guessed safety.
- L1: reset/reboot success and documented failure paths, using approved failure
  injection, target isolation and independently verified recovery.
- L2: no trustworthy normative state graph is established by these inputs.
  Reboot/readiness/firmware-query or reset/default-validation sequences require
  resolved citations, L2 gate entries, a persistent direct-access interface,
  readiness oracle and restoration procedure before executable authoring.
  There are no setters/getters for configuration defaults in the header.
- L3: no external actor or controllable stimulus is declared. Reboot through
  `Modem_Reboot` is a HAL action, not an external-stimulus L3 test. Do not assume
  relay/power-control capability or use the HAL result as independent stimulus
  proof. No L3 executable case is claimed.

The specification's Theory of operation section references
`cellular_modem_hal_init`, context handles, deinit and power up/down functions
that are not declared by the selected header. This conflicts with its earlier
statement of no explicit API dependencies. Resolve that contradiction before
creating lifecycle/state tests. No missing APIs or transitions are invented here.

## Coverage

HAL implementation line coverage: **N/A**.
HAL implementation branch coverage: **N/A**.

The checkout has a declaration-only HAL header and no HAL implementation
C/C++ files or vendor `.so`. Build/document helper scripts are not the HAL under
test. No implementation denominator exists in this checkout for gcov/lcov.
Static API signature checks: **3/3 (100%)**, not implementation coverage.
Runtime L1, L2 and L3 cases executed: **0**.

To measure real line/branch coverage, supply matching vendor implementation
sources and build configuration, then build with coverage instrumentation and
run authorized tests on the supported target. A binary alone permits access
testing but generally does not provide source-level coverage instrumentation.
Do not report Python test-code or mock/fixture coverage as HAL coverage.

## Local validation

Run from the workspace root:

    python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/ --collect-only -q
    python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/ -q

Execution results are recorded in the central README after validation.
