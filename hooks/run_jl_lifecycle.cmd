@echo off
setlocal EnableExtensions EnableDelayedExpansion

where python >nul 2>&1
if not errorlevel 1 (
    python -X utf8 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if not errorlevel 1 (
        python -X utf8 "%~dp0jl_lifecycle.py"
        set "JL_HOOK_EXIT=!errorlevel!"
        exit /b !JL_HOOK_EXIT!
    )
)

where python3 >nul 2>&1
if not errorlevel 1 (
    python3 -X utf8 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if not errorlevel 1 (
        python3 -X utf8 "%~dp0jl_lifecycle.py"
        set "JL_HOOK_EXIT=!errorlevel!"
        exit /b !JL_HOOK_EXIT!
    )
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -X utf8 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if not errorlevel 1 (
        py -3 -X utf8 "%~dp0jl_lifecycle.py"
        set "JL_HOOK_EXIT=!errorlevel!"
        exit /b !JL_HOOK_EXIT!
    )
)

>&2 echo JL Knowledge Base Skill requires Python 3.10 or newer for shared knowledge hooks.
exit /b 3
