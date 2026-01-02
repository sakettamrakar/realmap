# Analyze Parallel Scraping Logs
# Extracts failed listings and error summaries

param(
    [Parameter(Mandatory=$false)]
    [string]$LogsDir = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Log Analyzer for Parallel Scraping  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find latest logs directory if not specified
if ($LogsDir -eq "") {
    $latestDir = Get-ChildItem "logs\parallel_*" -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestDir) {
        $LogsDir = $latestDir.FullName
        Write-Host "Using latest logs: $LogsDir" -ForegroundColor Green
    } else {
        Write-Host "No logs directory found in logs\parallel_*" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Using specified logs: $LogsDir" -ForegroundColor Green
}

Write-Host ""

# Initialize summary
$summary = @{
    TotalPages = 0
    PagesWithErrors = 0
    TotalErrors = 0
    FailedListings = @()
    ErrorMessages = @{}
}

# Analyze each log file
$logFiles = Get-ChildItem "$LogsDir\*.log" -File
foreach ($logFile in $logFiles) {
    $summary.TotalPages++
    $pageName = $logFile.BaseName
    
    Write-Host "Analyzing $($logFile.Name)..." -ForegroundColor Yellow
    
    $content = Get-Content $logFile.FullName -Raw
    
    # Count errors
    $errorLines = $content | Select-String "ERROR" -AllMatches
    $errorCount = ($errorLines.Matches | Measure-Object).Count
    
    if ($errorCount -gt 0) {
        $summary.PagesWithErrors++
        $summary.TotalErrors += $errorCount
        Write-Host "  Found $errorCount errors" -ForegroundColor Red
        
        # Extract RERA IDs that failed
        $reraMatches = [regex]::Matches($content, "PCGRERA\d+")
        $reraIds = $reraMatches | ForEach-Object { $_.Value } | Select-Object -Unique
        
        # Look for specific error patterns
        if ($content -match "Failed to.*RERA:\s*(PCGRERA\d+)") {
            $failedId = $Matches[1]
            $summary.FailedListings += @{
                Page = $pageName
                RERA_ID = $failedId
            }
        }
        
        # Extract unique error messages
        $errorPatterns = [regex]::Matches($content, "ERROR\s+(.+?)(?=\n|$)")
        foreach ($match in $errorPatterns) {
            $errorMsg = $match.Groups[1].Value.Trim()
            if ($summary.ErrorMessages.ContainsKey($errorMsg)) {
                $summary.ErrorMessages[$errorMsg]++
            } else {
                $summary.ErrorMessages[$errorMsg] = 1
            }
        }
    } else {
        Write-Host "  No errors found" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Pages Analyzed: $($summary.TotalPages)" -ForegroundColor White
Write-Host "Pages with Errors: $($summary.PagesWithErrors)" -ForegroundColor $(if ($summary.PagesWithErrors -gt 0) { "Red" } else { "Green" })
Write-Host "Total Error Count: $($summary.TotalErrors)" -ForegroundColor $(if ($summary.TotalErrors -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($summary.FailedListings.Count -gt 0) {
    Write-Host "Failed Listings:" -ForegroundColor Red
    foreach ($failed in $summary.FailedListings) {
        Write-Host "  [$($failed.Page)] $($failed.RERA_ID)" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($summary.ErrorMessages.Count -gt 0) {
    Write-Host "Top Errors:" -ForegroundColor Red
    $summary.ErrorMessages.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
        Write-Host "  [$($_.Value)x] $($_.Key)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Full logs available at: $LogsDir" -ForegroundColor Cyan

# Save summary to file
$summaryFile = Join-Path $LogsDir "analysis_summary.txt"
$summaryContent = @"
========================================
  LOG ANALYSIS SUMMARY
========================================
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Logs Directory: $LogsDir

Total Pages Analyzed: $($summary.TotalPages)
Pages with Errors: $($summary.PagesWithErrors)
Total Error Count: $($summary.TotalErrors)

"@

if ($summary.FailedListings.Count -gt 0) {
    $summaryContent += "`nFailed Listings:`n"
    foreach ($failed in $summary.FailedListings) {
        $summaryContent += "  [$($failed.Page)] $($failed.RERA_ID)`n"
    }
}

if ($summary.ErrorMessages.Count -gt 0) {
    $summaryContent += "`nTop Errors:`n"
    $summary.ErrorMessages.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
        $summaryContent += "  [$($_.Value)x] $($_.Key)`n"
    }
}

$summaryContent | Out-File $summaryFile -Encoding UTF8
Write-Host "Summary saved to: $summaryFile" -ForegroundColor Green
