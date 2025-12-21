# Backend API Test Script for MySQL
# Tests all routes from test.rest using curl/Invoke-WebRequest

$baseUrl = "http://localhost:8000"
$mysqlDbName = "chapter1"
$mysqlUrl = "mysql://root:root@localhost:3306/chapter1"

Write-Host "=== Testing Backend API (MySQL) ===" -ForegroundColor Green
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

# Test 3: Add MySQL Database Connection
Write-Host "3. Testing PUT /api/v1/dbs/$mysqlDbName (add MySQL database)..." -ForegroundColor Yellow
try {
    $body = @{
        url = $mysqlUrl
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$mysqlDbName" `
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
Write-Host "4. Testing GET /api/v1/dbs (after adding MySQL)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: Refresh MySQL Database Metadata
Write-Host "5. Testing POST /api/v1/dbs/$mysqlDbName/refresh (refresh metadata)..." -ForegroundColor Yellow
Write-Host "   This may take a while..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$mysqlDbName/refresh" `
        -Method POST `
        -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   Database: $($content.name)" -ForegroundColor Cyan
    Write-Host "   Metadata keys: $($content.metadata.PSObject.Properties.Name -join ', ')" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response Body: $responseBody" -ForegroundColor Red
    }
}
Write-Host ""

# Test 6: Get MySQL Database Metadata
Write-Host "6. Testing GET /api/v1/dbs/$mysqlDbName (metadata)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$mysqlDbName" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   Database: $($content.name)" -ForegroundColor Cyan
    Write-Host "   Tables count: $($content.metadata.tables.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   (Metadata may not be ready yet)" -ForegroundColor Yellow
    }
}
Write-Host ""

# Test 7: Get MySQL Database Tables
Write-Host "7. Testing GET /api/v1/dbs/$mysqlDbName/tables..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$mysqlDbName/tables" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   Schemas: $($content.schemas.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Test 8: Execute MySQL SQL Query
Write-Host "8. Testing POST /api/v1/dbs/$mysqlDbName/query (SELECT * FROM employees)..." -ForegroundColor Yellow
try {
    $body = @{
        sql = "SELECT * FROM employees LIMIT 5"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$mysqlDbName/query" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   Columns: $($content.columns -join ', ')" -ForegroundColor Cyan
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

# Test 9: Natural Language Query
Write-Host "9. Testing POST /api/v1/dbs/$mysqlDbName/query/natural..." -ForegroundColor Yellow
try {
    $body = @{
        prompt = "查询 employees 表的所有信息"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$mysqlDbName/query/natural" -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   Generated SQL: $($content.sql)" -ForegroundColor Cyan
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

# Test 10: Error Test - Invalid SQL (INSERT not allowed)
Write-Host "10. Testing POST /api/v1/dbs/$mysqlDbName/query (INSERT - should fail)..." -ForegroundColor Yellow
try {
    $body = @{
        sql = "INSERT INTO employees VALUES (1, 'Test', 'User')"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/dbs/$mysqlDbName/query" -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
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

Write-Host "=== Backend API Tests Complete ===" -ForegroundColor Green

