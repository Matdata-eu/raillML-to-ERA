# Run ERA CONSTRUCT Queries
# Executes all ERA ontology CONSTRUCT queries and loads results into target endpoint

Write-Host "ERA Ontology CONSTRUCT Query Execution" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python not found. Please install Python 3." -ForegroundColor Red
    exit 1
}

# Check if requests module is installed
python -c "import requests" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing required Python packages..." -ForegroundColor Yellow
    pip install requests
}

# Run the script
python run-construct.py
