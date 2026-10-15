/*
 * Copyright 2026 RDK Management
 * SPDX-License-Identifier: Apache-2.0
 *
 * L1 test: cellular_hal_profile_modify rejects a NULL profile.
 *
 * Source contract: rdkb-halif-cellular-348946/include/cellular_hal.h:
 * "If NULL then return error."
 * The header defines RETURN_ERROR, although its prose says RETURN_ERR.
 *
 * This test supplies only an upper-layer callback, not a HAL implementation.
 * Runtime verification requires the vendor HAL or the companion cellular test
 * repository's implementation and its normal backend dependencies. This
 * interface-only checkout cannot provide those dependencies.
 *
 * From the workspace root, compile-check without linking:
 * cc -std=c11 -Wall -Wextra -Werror -pedantic \
 *    -Irdkb-halif-cellular-348946/include \
 *    -fsyntax-only \
 *    rdkb-tests/rdkb-halif-cellular-348946/test_cellular_profile_modify.c
 *
 * To execute, compile this source with the same include flags and link the
 * cellular HAL implementation and its backend dependencies, setting the output
 * filename with -o /tmp/test_cellular_profile_modify. Then run:
 * /tmp/test_cellular_profile_modify
 *
 * Expected success: PASS: cellular_hal_profile_modify rejects NULL profile
 * Failure: reports the actual and expected return codes on stderr.
 * Exit status: zero on success, nonzero on assertion failure.
 *
 * No initialization is performed: invalid input must be rejected at the API
 * boundary. No positive-path, device, or full-suite coverage is claimed.
 */

#include "cellular_hal.h"

/* Upper-layer test callback; its signature is checked by the HAL prototype. */
static int profile_status_callback(
    char *profile_id,
    CellularPDPType_t pdp_type,
    CellularDeviceProfileSelectionStatus_t profile_status)
{
    (void)profile_id;
    (void)pdp_type;
    (void)profile_status;
    return RETURN_OK;
}

/* PUBLIC_INTERFACE */
/**
 * Run the isolated NULL-profile contract check.
 *
 * Takes no parameters. Returns EXIT_SUCCESS if the HAL returns RETURN_ERROR,
 * or EXIT_FAILURE otherwise. This test does not emulate the function tested.
 */
int main(void)
{
    const int result =
        cellular_hal_profile_modify(NULL, profile_status_callback);

    /* Explicit checking keeps the assertion active even with NDEBUG defined. */
    if (result != RETURN_ERROR) {
        fprintf(stderr,
                "FAIL: cellular_hal_profile_modify(NULL, callback): "
                "expected %d, got %d\n",
                RETURN_ERROR, result);
        return EXIT_FAILURE;
    }

    puts("PASS: cellular_hal_profile_modify rejects NULL profile");
    return EXIT_SUCCESS;
}
