/*
 * Cellular modem HAL L1 contract tests.
 *
 * Build prerequisites: C11, ut-core's CUnit variant, and an isolated
 * cellular-modem HAL implementation with hardware dependencies stubbed.
 * This repository supplies declarations only; do not replace the functions
 * under test with preset-return mocks and interpret that as HAL coverage.
 *
 * Run the linked binary with -b (basic) or -a (automated), never console mode.
 * No reset or reboot is invoked by this suite.
 */

#include <stddef.h>
#include <stdlib.h>

#include <CUnit/CUnit.h>
#include <ut.h>

#include "cellular_modem_hal_api.h"

/* These unevaluated checks validate declarations without invoking hardware. */
_Static_assert(
    _Generic(&Modem_FactoryReset, int (*)(void): 1, default: 0),
    "Modem_FactoryReset must have signature int (void)");
_Static_assert(
    _Generic(&Modem_Reboot, int (*)(void): 1, default: 0),
    "Modem_Reboot must have signature int (void)");
_Static_assert(
    _Generic(&Modem_Firmware_Version, int (*)(char *): 1, default: 0),
    "Modem_Firmware_Version must have signature int (char *)");
_Static_assert(STATUS_SUCCESS == 0, "Documented success code must be zero");
_Static_assert(STATUS_FAILED == -1, "Documented failure code must be minus one");

/**
 * Verify that the firmware getter rejects a missing output buffer.
 *
 * NULL cannot satisfy the documented minimum 128-byte buffer requirement.
 * Do not assert output preservation on failure: the header does not promise it.
 */
static void Modem_Firmware_Version_negative_null_buffer(void)
{
    const int result = Modem_Firmware_Version(NULL);

    UT_ASSERT_EQUAL(result, STATUS_FAILED);
}

/**
 * Register only L1 cases and propagate every registration failure.
 *
 * Positive and minimum-buffer tests require a deterministic firmware fixture.
 * Error injection requires a lower-level shim, not a mock of the public API.
 * Reset/reboot have no input boundary or invalid-parameter cases.
 */
static int register_cellular_modem_l1(void)
{
    UT_test_suite_t *suite = UT_add_suite_withGroupID(
        "[L1 CellularModem]", NULL, NULL, UT_TESTS_L1);

    if (suite == NULL) {
        return -1;
    }

    if (UT_add_test(suite,
                    "Modem_Firmware_Version_negative_null_buffer",
                    Modem_Firmware_Version_negative_null_buffer) == NULL) {
        return -1;
    }

    return 0;
}

/* PUBLIC_INTERFACE */
/**
 * Initialize ut-core, register L1 tests, and return a CI-usable exit status.
 *
 * @param argc Number of command-line arguments.
 * @param argv Arguments accepted by ut-core; use -b or -a for CI execution.
 * @return EXIT_SUCCESS only when registration, execution, and assertions pass;
 *         EXIT_FAILURE otherwise.
 */
int main(int argc, char **argv)
{
    UT_status_t result;

    if (UT_init(argc, argv) != UT_STATUS_OK) {
        UT_exit();
        return EXIT_FAILURE;
    }

    if (register_cellular_modem_l1() != 0) {
        UT_exit();
        return EXIT_FAILURE;
    }

    result = UT_run_tests();

    /*
     * Check assertion failures explicitly rather than relying solely on the
     * framework status. CUnit retains its run summary after registry cleanup.
     */
    if (result != UT_STATUS_OK) {
        UT_exit();
        return EXIT_FAILURE;
    }

    return CU_get_number_of_failures() == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
