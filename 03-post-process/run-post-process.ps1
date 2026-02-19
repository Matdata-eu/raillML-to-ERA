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
$outputTtlFile = "era-graph-enriched.ttl"
$inputTtlFile = "..\02-construct\era-graph.ttl"

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

# Step 1: Add temporal data (if add-temporal.sparql exists and has content)
if (Test-Path "add-temporal.sparql") {
    $temporalQuery = Get-Content "add-temporal.sparql" -Raw
    if ($temporalQuery.Trim().Length -gt 0) {
        Write-Host "Step 1: Adding temporal data..." -ForegroundColor Green
        
        if ($fusekiAvailable) {
            try {
                $updateBody = "update=$([System.Uri]::EscapeDataString($temporalQuery))"
                
                $null = Invoke-RestMethod -Uri $fusekiUpdateEndpoint `
                    -Method POST `
                    -ContentType "application/x-www-form-urlencoded" `
                    -Body $updateBody `
                    -ErrorAction Stop
                
                Write-Host "  ✓ Temporal data added successfully" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️  WARNING: Failed to add temporal data: $_" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ⚠️  Skipped (Fuseki not available)" -ForegroundColor Yellow
        }
        Write-Host ""
    } else {
        Write-Host "Step 1: Skipping temporal data (add-temporal.sparql is empty)" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "Step 1: Skipping temporal data (add-temporal.sparql not found)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 1b: Infer part relations for linear infrastructure
if (Test-Path "infer-part-relations-linear.sparql") {
    $partRelationsLinearQuery = Get-Content "infer-part-relations-linear.sparql" -Raw
    if ($partRelationsLinearQuery.Trim().Length -gt 0) {
        Write-Host "Step 1b: Inferring isPartOf and hasPart relations (linear infrastructure)..." -ForegroundColor Green
        
        if ($fusekiAvailable) {
            try {
                $updateBody = "update=$([System.Uri]::EscapeDataString($partRelationsLinearQuery))"
                
                $null = Invoke-RestMethod -Uri $fusekiUpdateEndpoint `
                    -Method POST `
                    -ContentType "application/x-www-form-urlencoded" `
                    -Body $updateBody `
                    -ErrorAction Stop
                
                Write-Host "  ✓ Linear part relations inferred successfully" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️  WARNING: Failed to infer linear part relations: $_" -ForegroundColor Yellow
                Write-Host "     Error: $_" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ⚠️  Skipped (Fuseki not available)" -ForegroundColor Yellow
        }
        Write-Host ""
    } else {
        Write-Host "Step 1b: Skipping linear part relations inference (infer-part-relations-linear.sparql is empty)" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "Step 1b: Skipping linear part relations inference (infer-part-relations-linear.sparql not found)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 1c: Infer part relations for point infrastructure
if (Test-Path "infer-part-relations-point.sparql") {
    $partRelationsPointQuery = Get-Content "infer-part-relations-point.sparql" -Raw
    if ($partRelationsPointQuery.Trim().Length -gt 0) {
        Write-Host "Step 1c: Inferring isPartOf and hasPart relations (point infrastructure)..." -ForegroundColor Green
        
        if ($fusekiAvailable) {
            try {
                $updateBody = "update=$([System.Uri]::EscapeDataString($partRelationsPointQuery))"
                
                $null = Invoke-RestMethod -Uri $fusekiUpdateEndpoint `
                    -Method POST `
                    -ContentType "application/x-www-form-urlencoded" `
                    -Body $updateBody `
                    -ErrorAction Stop
                
                Write-Host "  ✓ Point part relations inferred successfully" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️  WARNING: Failed to infer point part relations: $_" -ForegroundColor Yellow
                Write-Host "     Error: $_" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ⚠️  Skipped (Fuseki not available)" -ForegroundColor Yellow
        }
        Write-Host ""
    } else {
        Write-Host "Step 1c: Skipping point part relations inference (infer-part-relations-point.sparql is empty)" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "Step 1c: Skipping point part relations inference (infer-part-relations-point.sparql not found)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 1d: Add missing rdf:type declarations
if (Test-Path "add-missing-rdf-types.sparql") {
    $addTypesQuery = Get-Content "add-missing-rdf-types.sparql" -Raw
    if ($addTypesQuery.Trim().Length -gt 0) {
        Write-Host "Step 1d: Adding missing rdf:type declarations..." -ForegroundColor Green
        
        if ($fusekiAvailable) {
            try {
                $updateBody = "update=$([System.Uri]::EscapeDataString($addTypesQuery))"
                
                $null = Invoke-RestMethod -Uri $fusekiUpdateEndpoint `
                    -Method POST `
                    -ContentType "application/x-www-form-urlencoded" `
                    -Body $updateBody `
                    -ErrorAction Stop
                
                Write-Host "  ✓ Missing rdf:type declarations added successfully" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️  WARNING: Failed to add missing rdf:type declarations: $_" -ForegroundColor Yellow
                Write-Host "     Error: $_" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ⚠️  Skipped (Fuseki not available)" -ForegroundColor Yellow
        }
        Write-Host ""
    } else {
        Write-Host "Step 1d: Skipping missing rdf:type declarations (add-missing-rdf-types.sparql is empty)" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "Step 1d: Skipping missing rdf:type declarations (add-missing-rdf-types.sparql not found)" -ForegroundColor Yellow
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

# Run geometry enrichment script
Write-Host "  Running enrich-geometries.py with: $venvPython" -ForegroundColor Cyan
& $venvPython enrich-geometries.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Geometry enrichment failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "  ✓ Geometry enrichment completed" -ForegroundColor Green
Write-Host ""

# Step 3: Finalizing output
Write-Host "Step 3: Finalizing output..." -ForegroundColor Green

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
        
        # Save to file
        $turtleData | Out-File -FilePath $outputTtlFile -Encoding UTF8
        
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
