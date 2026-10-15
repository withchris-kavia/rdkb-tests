# Bridge-util L1 coverage checkpoint

Repository: `rdkb-halif-bridge-util-348946`.
Capability: headers/specification only; no local implementation, binding, native
UT directory, or lower-level isolation shim was found.
Framework: Python/pytest driving GNU C11 syntax-only compiler probes.
Sources: `include/bridge_util_hal.h`, `include/network_interface.h`, and
`docs/pages/BridgeUtilHalSpec.md` in the source repository.
Feature scope: all eight combinations of `WIFI_MANAGE_SUPPORTED`,
`AMENITIES_NETWORK_ENABLED`, and `_CBR2_PRODUCT_REQ_`.

## Inventory and coverage obligations

All seven APIs are declared in `bridge_util_hal.h`; `network_interface.h`
declares data contracts but no public functions. Every API has a declaration
check in each of the eight new feature-configuration cases.

| API / signature | Results / contract | Positive | Negative | Boundary | Error-return |
| --- | --- | --- | --- | --- | --- |
| `int updateBridgeInfo(bridgeDetails *, char *, int, int)` | 0/-1; terminated interface name; INTERFACE_TYPE; OVS_CMD unavailable | BLOCKED | SPEC_UNCLEAR: rejection/NULL rules | BLOCKED plus SPEC_UNCLEAR: operation values | BLOCKED |
| `int checkIfExists(char *)` | 0 existing / -1 absent | BLOCKED | SPEC_UNCLEAR: invalid name/NULL | SPEC_UNCLEAR: name limits | BLOCKED |
| `void removeIfaceFromList(char *, const char *)` | Removes entry; absent entry is no-op | BLOCKED | SPEC_UNCLEAR: NULL/invalid strings | BLOCKED: first/last/only/absent cases need implementation | SPEC_UNCLEAR: void result and failure behavior |
| `int checkIfExistsInBridge(char *, char *)` | 0/-1 membership result | BLOCKED | SPEC_UNCLEAR: invalid name/NULL | SPEC_UNCLEAR: name limits | BLOCKED |
| `int HandlePreConfigVendor(bridgeDetails *, int)` | 0/-1; enum Config; before update | BLOCKED | SPEC_UNCLEAR: invalid Config/NULL rejection | BLOCKED: feature-specific valid Config edges | BLOCKED |
| `int HandlePostConfigVendor(bridgeDetails *, int)` | 0/-1; enum Config; after update | BLOCKED | SPEC_UNCLEAR: invalid Config/NULL rejection | BLOCKED: feature-specific valid Config edges | BLOCKED |
| `char *getVendorIfaces()` | Terminated string or NULL for no interfaces; C unspecified parameter list | BLOCKED | N/A: no documented input parameters | BLOCKED: no-interface case; string ownership/size unclear | SPEC_UNCLEAR: NULL denotes no interfaces, not documented failure |

Examples in comments are not exhaustive ranges. No NULL calls, destructive bridge
changes, unbounded pointer reads, or preset-return HAL mocks are used.
The specification's generic error-return wording does not define error semantics
for the void-return removal API. The actual declaration remains authoritative.

## Case mapping

New module: `test_bridge_util_l1_contract.py`.
- `test_l1_api_types_across_feature_configurations`: eight contract cases,
  each asserting seven API pointer types.
- `test_l1_conditional_symbol_visibility`: 32 contract cases covering four
  feature-gated symbols in eight configurations; failed compiler probes are
  expected absence assertions, not HAL runtime failures.
- `test_l1_external_global_types_and_capacities`: one contract case.

Existing `test_bridge_util_l1.py` remains unchanged with 23 contract checks.
No behavioral cases are authored because there is no safe implementation interface.
No metadata-only cases are counted as tests.

## Verification

Executed from the workspace root:

```sh
python -m pytest rdkb-tests/rdkb-halif-bridge-util-348946/test_bridge_util_l1_contract.py --collect-only -q
python -m pytest rdkb-tests/rdkb-halif-bridge-util-348946/test_bridge_util_l1_contract.py rdkb-tests/rdkb-halif-bridge-util-348946/test_bridge_util_l1.py -q
```

Observed: 41 new cases collected; combined execution reported 64 passed in
12.51 seconds, exit 0. This comprises 41 new and 23 existing contract checks,
with zero failures, skips, or not-run cases in the selected modules.
The new API-type cases provide eight passing contract checks per API.
All probes are syntax-only; no vendor binary, live hardware, or L2 test ran.

## Coverage metrics

API inventory: 7. APIs with passing behavioral cases: 0/7.
Fully behaviorally covered APIs: 0/7.
Behavioral axis coverage: 0/27 (28 cells minus one justified N/A input axis).
Behavioral executions: 0; behavioral pass rate: N/A.
Documented return outcomes: ten 0/-1 outcomes for five int-return APIs, plus
non-NULL/NULL for the getter; covered behaviorally: 0/12. The void API has no
documented return result. No statement/branch coverage was measured.
Contract cases written in this change: 41. New cases collected/executed/passed:
41/41/41. Total selected contract checks executed/passed: 64/64.
Contract-check pass rate: 100%; this is not HAL behavioral coverage.

## Resume / next obligation

Obtain the real vendor implementation and verified lower-level isolation support
plus a supported Python binding or safe executable interface. Then implement
documented success/no-op/membership cases and injected dependency failures.
Resolve NULL rejection, OVS_CMD, name limits, and returned-pointer ownership before
asserting those behaviors. Reconcile header/configuration and fixture identities
before resuming; rerun affected checks rather than inheriting historical passes.
