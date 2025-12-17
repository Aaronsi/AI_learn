# Backend API Test Script
# Tests all routes from test.rest using curl/Invoke-WebRequest

$baseUrl = "http://localhost:8000"
$dbName = "postgres"

Write-Host "=== Testing Backend API ===" -ForegroundColor Green
Write-Host ""

# Test 1: Health Check
Write-Host "1. Testing Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/health" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Get All Databases (Empty initially)
Write-Host "2. Testing GET /api/v1/dbs (should be empty)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: Add/Update Database Connection
Write-Host "3. Testing PUT /api/v1/dbs/$dbName (add database)..." -ForegroundColor Yellow
try {
    $body = @{
        url = "postgresql://postgres:postgres@localhost:5432/postgres"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$dbName" `
        -Method PUT `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response Body: $responseBody" -ForegroundColor Red
    }
}
Write-Host ""

# Test 4: Get All Databases (After adding)
Write-Host "4. Testing GET /api/v1/dbs (after adding)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: Get Database Metadata (may need to wait)
Write-Host "5. Testing GET /api/v1/dbs/$dbName (metadata)..." -ForegroundColor Yellow
Write-Host "   Waiting 3 seconds for metadata to be fetched..." -ForegroundColor Gray
Start-Sleep -Seconds 3
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$dbName" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   Database: $($content.name)" -ForegroundColor Cyan
    Write-Host "   Metadata keys: $($content.metadata.PSObject.Properties.Name -join ', ')" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   (Metadata may not be ready yet, this is expected)" -ForegroundColor Yellow
    }
}
Write-Host ""

# Test 6: Execute SQL Query
Write-Host "6. Testing POST /api/v1/dbs/$dbName/query (SELECT version())..." -ForegroundColor Yellow
try {
    $body = @{
        sql = "SELECT version()"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$dbName/query" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response Body: $responseBody" -ForegroundColor Red
    }
}
Write-Host ""

# Test 7: Execute SQL Query - Select from table
Write-Host "7. Testing POST /api/v1/dbs/$dbName/query (SELECT from information_schema)..." -ForegroundColor Yellow
try {
    $body = @{
        sql = "SELECT * FROM information_schema.tables LIMIT 5"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$dbName/query" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   Rows returned: $($content.rows.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response Body: $responseBody" -ForegroundColor Red
    }
}
Write-Host ""

# Test 8: Execute SQL Query - Test LIMIT auto-add
Write-Host "8. Testing POST /api/v1/dbs/$dbName/query (auto-add LIMIT)..." -ForegroundColor Yellow
try {
    $body = @{
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$dbName/query" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   Rows returned: $($content.rows.Count)" -ForegroundColor Cyan
    Write-Host "   (Should be limited to 100 rows)" -ForegroundColor Gray
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Test 11: Error Test - Invalid SQL (INSERT not allowed)
Write-Host "11. Testing POST /api/v1/dbs/$dbName/query (INSERT - should fail)..." -ForegroundColor Yellow
try {
    $body = @{
        sql = "INSERT INTO test VALUES (1)"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$dbName/query" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Red
    Write-Host "   (Should have failed)" -ForegroundColor Red
} catch {
    Write-Host "   Status: $($_.Exception.Response.StatusCode.value__) (Expected)" -ForegroundColor Green
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response: $responseBody" -ForegroundColor Cyan
    }
}
Write-Host ""

# Test 12: Error Test - SQL Syntax Error
Write-Host "12. Testing POST /api/v1/dbs/$dbName/query (Syntax error - should fail)..." -ForegroundColor Yellow
try {
    $body = @{
        sql = "SELECT * FROM WHERE"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$dbName/query" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Red
} catch {
    Write-Host "   Status: $($_.Exception.Response.StatusCode.value__) (Expected)" -ForegroundColor Green
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response: $responseBody" -ForegroundColor Cyan
    }
}
Write-Host ""

# Test 13: Error Test - Non-existent Database
Write-Host "13. Testing GET /api/v1/dbs/nonexistent_db (should return 404)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/nonexistent_db" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Red
} catch {
    Write-Host "   Status: $($_.Exception.Response.StatusCode.value__) (Expected 404)" -ForegroundColor Green
}
Write-Host ""

Write-Host "=== Backend API Tests Complete ===" -ForegroundColor Green

