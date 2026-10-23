"""Static modem contract regression checks, not runtime L1/L2/L3 acceptance."""
from pathlib import Path
import shutil
import subprocess

import pytest

REPOSITORY = (
    Path(__file__).resolve().parents[2] / "rdkb-halif-cellular-modem-348946"
)
HEADER = REPOSITORY / "include" / "cellular_modem_hal_api.h"

# Explicit expectations from the published header, not parser-generated manifests.
SIGNATURES = {
    "Modem_FactoryReset": "void",
    "Modem_Reboot": "void",
    "Modem_Firmware_Version": "char *",
}
LANGUAGES = ("c", "c++")


@pytest.fixture(scope="module", params=LANGUAGES)
# PUBLIC_INTERFACE
def language_compiler(request):
    """Require the real host compiler for each language; missing tools fail setup."""
    language = request.param
    compiler = shutil.which("cc" if language == "c" else "c++")
    assert compiler, f"Required {language} compiler is missing"
    assert HEADER.is_file(), f"Source contract missing: {HEADER}"
    return language, compiler


def _compile(language_compiler, body):
    language, compiler = language_compiler
    standard = "c11" if language == "c" else "c++11"
    return subprocess.run(
        [
            compiler, f"-std={standard}", "-Wall", "-Wextra", "-Werror",
            "-pedantic", "-fsyntax-only", "-x", language,
            "-I", str(HEADER.parent), "-",
        ],
        input='#include "cellular_modem_hal_api.h"\n' + body,
        capture_output=True, text=True, cwd=REPOSITORY, timeout=20,
    )


def _assert_compiles(language_compiler, body):
    result = _compile(language_compiler, body)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("symbol,arguments", SIGNATURES.items())
# PUBLIC_INTERFACE
def test_public_api_signature(language_compiler, symbol, arguments):
    """M-API: pin all three published return and parameter types in C and C++."""
    _assert_compiles(
        language_compiler,
        f"int (*modem_contract_probe)({arguments}) = &{symbol};\n",
    )


@pytest.mark.parametrize(
    "name,value", [("STATUS_SUCCESS", 0), ("STATUS_FAILED", -1)]
)
# PUBLIC_INTERFACE
def test_status_constant(language_compiler, name, value):
    """M-STATUS: preserve the documented success and failure values."""
    language, _ = language_compiler
    keyword = "_Static_assert" if language == "c" else "static_assert"
    _assert_compiles(
        language_compiler, f'{keyword}({name} == ({value}), "{name} changed");\n'
    )


# PUBLIC_INTERFACE
def test_header_is_self_contained_and_repeatable(language_compiler):
    """M-INCLUDE: consumers can include the header twice without prerequisites."""
    _assert_compiles(
        language_compiler,
        '#include "cellular_modem_hal_api.h"\n'
        "int (*modem_contract_probe)(char *) = &Modem_Firmware_Version;\n",
    )


@pytest.mark.parametrize(
    "body",
    [
        "void (*modem_contract_probe)(void) = &Modem_Reboot;\n",
        "int (*modem_contract_probe)(char **) = &Modem_Firmware_Version;\n",
        "int (*modem_contract_probe)(unsigned int) = &Modem_FactoryReset;\n",
    ],
    ids=["wrong-return", "wrong-buffer-pointer-depth", "wrong-reset-parameters"],
)
# PUBLIC_INTERFACE
def test_incompatible_declaration_rejected(language_compiler, body):
    """M-API: incompatible consumer types must produce compiler diagnostics."""
    result = _compile(language_compiler, body)
    assert result.returncode != 0, "Compiler accepted an incompatible declaration"
    assert "error:" in result.stderr.lower(), result.stderr


# PUBLIC_INTERFACE
def test_cpp_declarations_have_c_linkage():
    """M-LINKAGE: C++ consumers must see all three APIs with C language linkage."""
    compiler = shutil.which("c++")
    assert compiler, "Required C++ compiler is missing"
    # Without the header's extern-C block these redeclarations conflict with
    # prior C++ linkage. This checks the real header without defining a fake HAL.
    body = 'extern "C" {\n' + "".join(
        f"int {symbol}({arguments});\n"
        for symbol, arguments in SIGNATURES.items()
    ) + "}\n"
    _assert_compiles(("c++", compiler), body)
