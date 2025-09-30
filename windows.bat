@echo off
REM user_data.bat - EC2 initialization script for Windows
SETLOCAL ENABLEDELAYEDEXPANSION

REM ===== Update system (Windows Updates) =====
echo Starting Windows Update...
powershell -Command "Install-WindowsUpdate -AcceptAll -IgnoreReboot"
echo Windows Update completed.

REM ===== Install Docker =====
echo Installing Docker...
powershell -Command "Invoke-WebRequest -UseBasicParsing -Uri https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe -OutFile C:\Windows\Temp\DockerInstaller.exe"
powershell -Command "Start-Process -FilePath C:\Windows\Temp\DockerInstaller.exe -ArgumentList '/quiet' -Wait"
echo Docker installation completed.

REM ===== Install Docker Compose (Docker Desktop includes it) =====
echo Docker Compose comes with Docker Desktop on Windows.

REM ===== Create application directory =====
mkdir C:\webapp

REM ===== Create a simple HTML file =====
SET ENVIRONMENT=dev
(
echo ^<!DOCTYPE html^>
echo ^<html^>
echo ^<head^>
echo ^    ^<title^>DevOps Demo - %ENVIRONMENT%^</title^>
echo ^</head^>
echo ^<body^>
echo ^    ^<h1^>DevOps Demo Application^</h1^>
echo ^    ^<p^>Environment: %ENVIRONMENT%^</p^>
echo ^    ^<p^>Instance: %COMPUTERNAME%^</p^>
echo ^    ^<p^>Region: (Set manually)^</p^>
echo ^</body^>
echo ^</html^>
) > C:\webapp\index.html

REM ===== Simple HTTP server via PowerShell =====
echo Starting simple HTTP server on port 80...
powershell -Command "Start-Process powershell -ArgumentList '-NoProfile -WindowStyle Hidden -Command {Add-Type -AssemblyName System.Net.HttpListener; $listener = New-Object System.Net.HttpListener; $listener.Prefixes.Add(\"http://*:80/\"); $listener.Start(); while ($true) { $ctx = $listener.GetContext(); $resp = $ctx.Response; $bytes = [System.IO.File]::ReadAllBytes(\"C:\\webapp\\index.html\"); $resp.ContentLength64 = $bytes.Length; $resp.OutputStream.Write($bytes,0,$bytes.Length); $resp.Close(); } }'"

REM ===== CloudWatch Agent =====
echo Installing CloudWatch Agent...
powershell -Command "Invoke-WebRequest -Uri https://s3.amazonaws.com/amazoncloudwatch-agent/windows/amd64/latest/AmazonCloudWatchAgent.zip -OutFile C:\Windows\Temp\AmazonCloudWatchAgent.zip"
powershell -Command "Expand-Archive -Path C:\Windows\Temp\AmazonCloudWatchAgent.zip -DestinationPath C:\Program Files\Amazon\AmazonCloudWatchAgent"
powershell -Command "C:\Program Files\Amazon\AmazonCloudWatchAgent\install.ps1"

REM ===== Log completion =====
echo User data script completed at %DATE% %TIME% >> C:\user-data.log
