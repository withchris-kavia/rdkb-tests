# Cellular HAL contract test matrix

Authoritative inputs: `rdkb-halif-cellular-348946/include/cellular_hal.h`
and `docs/pages/CellularHalSpec.md`, resolved from the workspace root.

These are static contract regression tests, not L1 runtime acceptance tests.
All 36 APIs are considered for L1, but runtime cases cannot execute without
the vendor implementation. No mocked HAL or fabricated implementation is used.

| Requirement ID | Source contract | Pytest function | Cases | Expected evidence |
|---|---|---|---|---|
| C-API | Header FUNCTION PROTOTYPES: 36 declarations | test_api_inventory, test_api_signature | Exact API set and every signature | Inventory equality and successful C11 type checking |
| C-API | C type system applied to declared APIs | test_incompatible_api_types_rejected | Wrong return, pointer depth, arity/types | Compiler rejects each incompatible declaration |
| C-CONSTANT | Header STRUCTURE AND CONSTANT DEFINITIONS | test_constant_value | 13 success/error, sentinel and buffer constants | C11 static assertions |
| C-BUFFER | Header string array members | test_buffer_capacity | 17 capacities, including 20-byte ICCID field | C11 sizeof assertions |
| C-ENUM | Header enum declarations | test_enum_values | 23 enums, all declared values | C11 static assertions |
| C-CALLBACK | Header callback typedefs | test_callback_signature | Seven callback types | Bidirectional function-pointer assignments compile |
| C-VARIANT | Header QMI_SUPPORT conditional and guarded macros | test_qmi_build_variant, test_guarded_macro_preserves_caller_definition | Full/lite and seven caller macro overrides | Preprocessor and static assertions |

Every case uses the source header directly, an isolated compiler subprocess with a
20-second tooling timeout, and no hardware, network or persistent state changes.
Compiler input is supplied on stdin with `-fsyntax-only`; no native test sources
or binaries are persisted. Repeated inclusion also checks the include guard.
The timeout is a test-tool bound, not a claimed HAL response-time requirement.

The dictionaries and parameter lists in the test module enumerate case inputs and
pytest identifiers. Requirement IDs in function docstrings map to this table.
No custom markers, configuration schema, device profiles or secrets are required.

## Runtime test gaps (not counted as passes or skips)

- L1: success and error returns, output data, input ranges, minimum/maximum and
  out-of-range handling for all APIs require `cellularmanager.so` or its source,
  an appropriate supported binding, and an isolated execution environment.
- Explicit NULL semantics require runtime tests: `profile_create(NULL, ...)`
  selects the default profile, `profile_modify(NULL, ...)` returns an error,
  and `start_network(..., NULL, ...)` uses the default profile.
- L2: initialization before operations, open/start/stop sequences, profile
  lifecycle, callback delivery and dependency failures need the real HAL.
- L3: external modem removal, SIM changes and controlled network stimuli require
  external equipment, declared capabilities, explicit opt-in and restoration.
- No runtime behavioral test is generated as a preset-return mock or an
  unconditional skip; static assertions do not establish any of these behaviors.

## Specification gaps

1. The header defines `RETURN_ERROR`, but return documentation uses undefined
   `RETURN_ERR`; no additional failure-code mapping should be invented.
2. RSRQ is an integer field but documents a fractional bound of -19.5.
3. Cell IDs document a 36-bit maximum while their fields use `unsigned int`;
   portability and representation need clarification.
4. The slot ICCID array has capacity 20, while the current ICCID getter documents
   a caller buffer of at least 21. These are distinct contracts, not assumed equal.
5. The specification says there are no asynchronous notifications, while the
   header exposes callbacks. Delivery timing and threading need clarification.
6. No explicit deinitialization API, precise operation timeouts, or complete
   per-function invalid-input/error and dependency-failure contracts are provided.

## Coverage scope

The repository supplies declarations, documentation and build/document helper
scripts, not a HAL C/C++ implementation. `build_ut.sh` downloads a separate suite;
it is not a HAL implementation and is not run by these tests.

HAL implementation line coverage: **N/A** (no instrumentable implementation).
HAL implementation branch coverage: **N/A** (no implementation control flow).

The suite checks 36/36 public function signatures (100% static API signature
coverage), seven callbacks, 23 enum types, 17 buffer capacities and 13 constants.
This is not executable line coverage, branch coverage, ABI compatibility across
architectures, runtime validation, or full behavioral coverage. Tooling-script
coverage is outside this suite's scope. Python test-code coverage must not be
reported as HAL implementation coverage.
