@echo off
echo 🚀 Starting Bangladesh Job Search Agent...
echo.

echo 📦 Starting FastAPI Backend...
start "Backend" cmd /k "python api_backend.py"

echo ⏳ Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo 🎨 Starting React Frontend...
cd react-frontend
start "Frontend" cmd /k "npm run dev"

echo.
echo ✅ Both services are starting!
echo 📱 Frontend: http://localhost:3000
echo 🔧 Backend: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo 💡 Press any key to open the application in your browser...
pause >nul

start http://localhost:3000

echo 🎉 Application opened in browser!
echo.
echo To stop the services, close the command windows or press Ctrl+C in each window.
pause
