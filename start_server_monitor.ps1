# ArcSpatialDB Server Monitor with Auto-Reconnect
# PowerShell script for Windows production deployment

param(
    [int]$MaxRetries = 10,
    [int]$RetryDelay = 30,
    [string]$LogFile = "server_monitor.log"
)

# Function to write to log
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

# Function to check if server is running
function Test-ServerRunning {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

# Function to start server
function Start-ArcSpatialDBServer {
    Write-Log "🚀 Starting ArcSpatialDB Server Monitor"
    Write-Log "📍 Max Retries: $MaxRetries"
    Write-Log "⏱️ Retry Delay: $RetryDelay seconds"
    Write-Log "📝 Log File: $LogFile"
    Write-Log "=" * 50

    $retryCount = 0
    $isRunning = $true

    while ($isRunning -and $retryCount -lt $MaxRetries) {
        try {
            Write-Log "🔄 Attempt $($retryCount + 1)/$MaxRetries"
            Write-Log "✅ Starting server process..."
            
            # Start the server process
            $process = Start-Process -FilePath "python" -ArgumentList "server_with_reconnect.py" -PassThru -NoNewWindow
            
            # Monitor the process
            while (-not $process.HasExited) {
                Start-Sleep -Seconds 5
                
                # Check if server is responding
                if (Test-ServerRunning) {
                    Write-Log "✅ Server is running and responding"
                }
            }
            
            # Process has exited
            $exitCode = $process.ExitCode
            Write-Log "⚠️ Server process exited with code: $exitCode"
            
        }
        catch {
            Write-Log "❌ Error starting server: $($_.Exception.Message)"
        }
        
        $retryCount++
        
        if ($retryCount -lt $MaxRetries) {
            Write-Log "⏳ Waiting $RetryDelay seconds before retry..."
            Start-Sleep -Seconds $RetryDelay
            
            # Increase delay for next retry (exponential backoff)
            $RetryDelay = [Math]::Min($RetryDelay * 2, 300)  # Max 5 minutes
        }
        else {
            Write-Log "❌ Maximum retries ($MaxRetries) reached. Server will not restart."
        }
    }
    
    if (-not $isRunning) {
        Write-Log "✅ Server monitor stopped by user"
    }
    else {
        Write-Log "❌ Server failed permanently after $MaxRetries attempts"
    }
}

# Handle Ctrl+C gracefully
$null = Register-EngineEvent PowerShell.Exiting -Action {
    Write-Log "🛑 Server monitor stopped by user"
    exit 0
}

# Start the server monitor
Start-ArcSpatialDBServer 