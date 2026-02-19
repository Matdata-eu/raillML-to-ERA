# SPARQL Anything Conversion Script
# This script runs the SPARQL query on the XML file to produce the RDF output

Write-Host "Converting railML XML to RDF using SPARQL Anything..." -ForegroundColor Green

# Run the SPARQL Anything docker container
docker run --rm `
    -v "${PWD}:/data" `
    -w /data `
    --entrypoint java `
    mathiasvda/sparql-anything `
    -jar /app/artifacts/sparql-anything-v1.1.2-beta.jar `
    -q one-eyed-graph.sparql `
    -f TTL `
    -o output/one-eyed-graph.ttl

if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Conversion completed successfully!" -ForegroundColor Green
    Write-Host "Output file: output/one-eyed-graph.ttl" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] Conversion failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Upload to Fuseki
Write-Host "`nUploading data to Fuseki..." -ForegroundColor Green

$fusekiUrl = "http://localhost:8082/jena-fuseki/advanced-example-one-eyed"
$fusekiDataEndpoint = "$fusekiUrl/data"

# Check if Fuseki is available
try {
    $testQuery = @{query='ASK { }'}
    $response = Invoke-WebRequest -Uri "$fusekiUrl/query" -Method POST -Body $testQuery -TimeoutSec 5 -ErrorAction Stop -UseBasicParsing
    Write-Host "  Fuseki is available" -ForegroundColor Cyan
} catch {
    Write-Host "[WARNING] Fuseki is not available at $fusekiUrl" -ForegroundColor Yellow
    Write-Host "  Skipping Fuseki upload. Data saved locally in output/one-eyed-graph.ttl" -ForegroundColor Yellow
    exit 0
}

# Upload the TTL file to Fuseki
try {
    $headers = @{
        "Content-Type" = "text/turtle"
    }
    
    $turtleData = Get-Content -Path "output/one-eyed-graph.ttl" -Raw -Encoding UTF8
    
    Invoke-RestMethod -Uri "$fusekiDataEndpoint`?default" `
        -Method POST `
        -Headers $headers `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($turtleData)) `
        -ErrorAction Stop
    
    Write-Host "[SUCCESS] Data uploaded to Fuseki successfully!" -ForegroundColor Green
    Write-Host "  Endpoint: $fusekiUrl" -ForegroundColor Cyan
} catch {
    Write-Host "[WARNING] Failed to upload to Fuseki: $_" -ForegroundColor Yellow
    Write-Host "  Data saved locally in output/one-eyed-graph.ttl" -ForegroundColor Yellow
}
