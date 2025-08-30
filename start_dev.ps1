# Bangladesh Job Search Agent - Development Launcher
Write-Host "🚀 Starting Bangladesh Job Search Agent..." -ForegroundColor Green
Write-Host ""

# Start FastAPI Backend
Write-Host "📦 Starting FastAPI Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python api_backend.py" -WindowStyle Normal

# Wait for backend to start
Write-Host "⏳ Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start React Frontend
Write-Host "🎨 Starting React Frontend..." -ForegroundColor Cyan
Set-Location react-frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev" -WindowStyle Normal

# Return to root directory
Set-Location ..

Write-Host ""
Write-Host "✅ Both services are starting!" -ForegroundColor Green
Write-Host "📱 Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "🔧 Backend: http://localhost:8000" -ForegroundColor White
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

# Ask user if they want to open the browser
$openBrowser = Read-Host "💡 Do you want to open the application in your browser? (y/n)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Write-Host "🌐 Opening application in browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:3000"
    Write-Host "🎉 Application opened in browser!" -ForegroundColor Green
}

Write-Host ""
Write-Host "To stop the services, close the PowerShell windows or press Ctrl+C in each window." -ForegroundColor Yellow
Write-Host "Press any key to exit this launcher..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
