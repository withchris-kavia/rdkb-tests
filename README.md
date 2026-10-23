# rdkb-tests

## rdkb-halif-cellular-348946

### Cellular HAL static contract regression suite

- Source repository: `rdkb-halif-cellular-348946`.
- Test: [test_cellular_contract.py](rdkb-halif-cellular-348946/test_cellular_contract.py).
- Matrix, requirement references and gaps:
  [TEST_MATRIX.md](rdkb-halif-cellular-348946/TEST_MATRIX.md).
- Constituent tests: `test_api_inventory`, `test_api_signature`,
  `test_constant_value`, `test_buffer_capacity`, `test_enum_values`,
  `test_callback_signature`, `test_qmi_build_variant`,
  `test_guarded_macro_preserves_caller_definition`,
  `test_incompatible_api_types_rejected`.
- Purpose: detect regressions in all 36 public function declarations, seven
  callback types, 23 enum types, 13 constants, 17 string array capacities,
  full/lite QMI configuration and guarded macro overrides. Negative cases ensure
  incompatible API use is rejected. No HAL function is called.
- Prerequisites: Python 3.10+, pytest, and a C11 compiler providing `cc` (GCC or
  Clang with POSIX development headers). Source folder must remain alongside
  `rdkb-tests/`. No native library, hardware, credentials, plugin or network is
  needed. Missing compiler is a test setup failure.
- Working directory: workspace root (`code-generation/`).
- Setup if pytest is absent: `python -m pip install --disable-pip-version-check pytest`.
- Collect: `python -m pytest rdkb-tests/rdkb-halif-cellular-348946/ --collect-only -q`.
- Run: `python -m pytest rdkb-tests/rdkb-halif-cellular-348946/ -q`.
- Possible success output: pytest reports collected cases passed, exit code 0.
- Possible failure output: assertion failure with compiler diagnostics or API
  inventory differences, exit code 1. Pytest exit codes: 2 interrupted,
  3 internal error, 4 usage error, 5 no tests collected.
- Verification status: local collection found 109 tests; execution reported
  `109 passed in 13.54s` (exit code 0), with no failures or skips.
- Coverage: HAL implementation line and branch coverage are **N/A**, because
  this is an interface-only repository without HAL implementation sources.
  Static checks must not be described as runtime HAL coverage.

## rdkb-halif-cellular-modem-348946

### Cellular-modem HAL static contract regression suite

- Source repository: `rdkb-halif-cellular-modem-348946`.
- Test: [test_modem_contract.py](rdkb-halif-cellular-modem-348946/test_modem_contract.py).
- Requirements, requested-skill dispositions, missing inputs and coverage:
  [TEST_MATRIX.md](rdkb-halif-cellular-modem-348946/TEST_MATRIX.md).
- Constituent tests: `test_public_api_signature`, `test_status_constant`,
  `test_header_is_self_contained_and_repeatable`,
  `test_incompatible_declaration_rejected`,
  `test_cpp_declarations_have_c_linkage`.
- Purpose: pin all three published API signatures and both status constants,
  verify C/C++ header usability and C linkage, and reject incompatible consumer
  types. These are static contract tests, not runtime L1/L2/L3 acceptance.
- Prerequisites: Python 3.10+, pytest, C11 `cc`, C++11 `c++` (GCC or Clang).
  Keep the source repository alongside `rdkb-tests/`. No hardware, credentials,
  network, library or pytest plugin is needed. Missing compilers fail setup.
- Working directory: workspace root (`code-generation/`).
- Setup if needed: `python -m pip install --disable-pip-version-check pytest`.
- Collect: `python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/ --collect-only -q`.
- Run: `python -m pytest rdkb-tests/rdkb-halif-cellular-modem-348946/ -q`.
- Possible success: collected static tests pass; pytest exit code 0.
- Possible failure: compiler diagnostics or changed constants/signatures produce
  assertion failure, exit code 1. Exit codes 2/3/4/5 mean interrupted/internal
  error/usage error/no tests collected respectively.
- Verification status: local collection found 19 cases; execution reported
  `19 passed in 0.48s` (exit code 0), with no failures or skips.
- HAL implementation line coverage: **N/A**; branch coverage: **N/A**.
  No HAL implementation sources or vendor library are present in the checkout.
  Static signature checks cover 3/3 declarations, not runtime behavior.
- Requested inventory/native/L2/L3 workflows remain blocked by missing required
  inputs, detailed in the linked matrix. The JSON client workflow does not
  apply to this C-only contract. No fabricated manifests, transports, passing
  runtime placeholders, device skips or destructive calls are introduced.
