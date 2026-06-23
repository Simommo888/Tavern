param(
    [switch]$NewSession,
    [string]$Session = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $env:VIMAX_LLM_API_KEY -and $env:OPENAI_API_KEY) {
    $env:VIMAX_LLM_API_KEY = $env:OPENAI_API_KEY
}

# Keep ViMax's Python child on the uv-managed Python 3.12 environment.
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $venvPython) {
    $env:VIMAX_PYTHON_CMD = $venvPython
    $env:VIMAX_AGENT_COMMAND = $null
    $env:VIMAX_AGENT_ARGS = $null
} else {
    $env:VIMAX_PYTHON_CMD = $null
    $env:VIMAX_AGENT_COMMAND = "uv"
    $env:VIMAX_AGENT_ARGS = "run python main_agent.py --jsonl --stdin-repl"
}

$argsList = @("run", "tui")
if ($NewSession) {
    $argsList += "--"
    $argsList += "--new-session"
} elseif ($Session) {
    $argsList += "--"
    $argsList += "--session"
    $argsList += $Session
}

Push-Location (Join-Path $root "ui")
try {
    npm @argsList
} finally {
    Pop-Location
}
