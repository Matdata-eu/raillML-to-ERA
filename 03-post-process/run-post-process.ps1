# Post-Processing Script
# This script runs post-processing steps on the ERA graph:
# 1. Add temporal data (if add-temporal.sparql is defined)
# 2. Enrich geometries using linear referencing

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "ERA Post-Processing Pipeline" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Configuration
$fusekiUrl = "http://localhost:8082/jena-fuseki/advanced-example"
$fusekiQueryEndpoint = "$fusekiUrl/query"
$fusekiUpdateEndpoint = "$fusekiUrl/update"
$fusekiDataEndpoint = "$fusekiUrl/data"
$outputTtlFile = "output/era-graph-enriched.ttl"
$inputTtlFile = "..\02-construct\output\era-graph.ttl"

# Check if Fuseki is available
$fusekiAvailable = $false
Write-Host "Checking Fuseki availability..." -ForegroundColor Yellow
try {
    # Use ASK query to test endpoint
    $testQuery = @{query='ASK { }'}
    $null = Invoke-WebRequest -Uri $fusekiQueryEndpoint -Method POST -Body $testQuery -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    $fusekiAvailable = $true
    Write-Host "  ✓ Fuseki is available" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  WARNING: Fuseki is not available at $fusekiUrl" -ForegroundColor Yellow
    Write-Host "     Results will only be saved to local file" -ForegroundColor Yellow
}
Write-Host ""

# Step 1: Execute SPARQL UPDATE queries
$sparqlUpdateDir = "sparql-update"
if (Test-Path $sparqlUpdateDir) {
    $sparqlFiles = Get-ChildItem -Path $sparqlUpdateDir -Filter "*.sparql" | Sort-Object Name
    
    if ($sparqlFiles.Count -gt 0) {
        Write-Host "Step 1: Executing SPARQL UPDATE queries from $sparqlUpdateDir..." -ForegroundColor Green
        Write-Host "  Found $($sparqlFiles.Count) SPARQL file(s)" -ForegroundColor Cyan
        Write-Host ""
        
        $stepCounter = 1
        foreach ($file in $sparqlFiles) {
            $stepLabel = "1.$([char](96 + $stepCounter))"
            $stepCounter++
            
            Write-Host "  Step $stepLabel`: Processing $($file.Name)..." -ForegroundColor Cyan
            
            $queryContent = Get-Content $file.FullName -Raw
            if ($queryContent.Trim().Length -eq 0) {
                Write-Host "    ⚠️  Skipped (file is empty)" -ForegroundColor Yellow
                continue
            }
            
            if ($fusekiAvailable) {
                try {
                    $updateBody = "update=$([System.Uri]::EscapeDataString($queryContent))"
                    
                    $null = Invoke-RestMethod -Uri $fusekiUpdateEndpoint `
                        -Method POST `
                        -ContentType "application/x-www-form-urlencoded" `
                        -Body $updateBody `
                        -ErrorAction Stop
                    
                    Write-Host "    ✓ Executed successfully" -ForegroundColor Green
                } catch {
                    Write-Host "    ⚠️  WARNING: Execution failed: $_" -ForegroundColor Yellow
                }
            } else {
                Write-Host "    ⚠️  Skipped (Fuseki not available)" -ForegroundColor Yellow
            }
        }
        Write-Host ""
    } else {
        Write-Host "Step 1: No SPARQL UPDATE queries found in $sparqlUpdateDir" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "Step 1: SPARQL UPDATE directory not found ($sparqlUpdateDir)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 2: Enrich geometries using linear referencing
Write-Host "Step 2: Enriching geometries using linear referencing..." -ForegroundColor Green

# Check if Python virtual environment exists
$venvPython = "..\..\venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "..\..\.venv\Scripts\python.exe"
}
if (-not (Test-Path $venvPython)) {
    Write-Host "  ⚠️  WARNING: Python virtual environment not found" -ForegroundColor Yellow
    Write-Host "     Using system Python" -ForegroundColor Yellow
    # Use the python command from PATH
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $venvPython) {
        Write-Host "  ❌ Python not found in PATH" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Apply data fixes
$dataFixesDir = "data-fixes"
if (Test-Path $dataFixesDir) {
    $fixFiles = Get-ChildItem -Path $dataFixesDir -Filter "*.sparql" | Sort-Object Name
    
    if ($fixFiles.Count -gt 0) {
        Write-Host "Step 3: Applying data fixes from $dataFixesDir..." -ForegroundColor Green
        Write-Host "  Found $($fixFiles.Count) fix file(s)" -ForegroundColor Cyan
        Write-Host ""
        
        $fixCounter = 1
        foreach ($file in $fixFiles) {
            $stepLabel = "3.$([char](96 + $fixCounter))"
            $fixCounter++
            
            Write-Host "  Step $stepLabel`: Processing $($file.Name)..." -ForegroundColor Cyan
            
            $queryContent = Get-Content $file.FullName -Raw
            if ($queryContent.Trim().Length -eq 0) {
                Write-Host "    ⚠️  Skipped (file is empty)" -ForegroundColor Yellow
                continue
            }
            
            if ($fusekiAvailable) {
                try {
                    $updateBody = "update=$([System.Uri]::EscapeDataString($queryContent))"
                    
                    $null = Invoke-RestMethod -Uri $fusekiUpdateEndpoint `
                        -Method POST `
                        -ContentType "application/x-www-form-urlencoded" `
                        -Body $updateBody `
                        -ErrorAction Stop
                    
                    Write-Host "    ✓ Applied successfully" -ForegroundColor Green
                } catch {
                    Write-Host "    ⚠️  WARNING: Failed to apply: $_" -ForegroundColor Yellow
                }
            } else {
                Write-Host "    ⚠️  Skipped (Fuseki not available)" -ForegroundColor Yellow
            }
        }
        Write-Host ""
    } else {
        Write-Host "Step 3: No data fixes found in $dataFixesDir" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "Step 3: Data fixes directory not found ($dataFixesDir)" -ForegroundColor Yellow
    Write-Host ""
}

# Run geometry enrichment script
Write-Host "  Running enrich-geometries.py with: $venvPython" -ForegroundColor Cyan
& $venvPython enrich-geometries.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Geometry enrichment failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "  ✓ Geometry enrichment completed" -ForegroundColor Green
Write-Host ""

# Step 4: Finalizing output
Write-Host "Step 4: Finalizing output..." -ForegroundColor Green

if ($fusekiAvailable) {
    try {
        # Query Fuseki to get all triples
        $query = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"
        
        $headers = @{
            "Accept" = "text/turtle"
        }
        
        $body = @{
            query = $query
        }
        
        $turtleData = Invoke-RestMethod -Uri $fusekiQueryEndpoint `
            -Method POST `
            -Headers $headers `
            -Body $body `
            -ErrorAction Stop
        
        # Save to file (UTF-8 without BOM; Out-File -Encoding UTF8 adds BOM in PS5)
        [System.IO.File]::WriteAllText(
            (Join-Path (Get-Location) $outputTtlFile),
            $turtleData,
            [System.Text.UTF8Encoding]::new($false)
        )
        
        Write-Host "  ✓ Exported from Fuseki to $outputTtlFile" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  WARNING: Failed to export from Fuseki: $_" -ForegroundColor Yellow
    }
} else {
    # When using local files, the Python script already created the enriched file
    if (Test-Path $outputTtlFile) {
        Write-Host "  ✓ Output file ready: $outputTtlFile" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Output file not found: $outputTtlFile" -ForegroundColor Red
    }
}

Write-Host ""

# Summary
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "POST-PROCESSING SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

if ($fusekiAvailable) {
    Write-Host "✓ Results saved to Fuseki: $fusekiUrl" -ForegroundColor Green
}
Write-Host "✓ Results saved to file: $outputTtlFile" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Post-processing complete!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan
