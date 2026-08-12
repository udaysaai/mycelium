@echo off
title Mycelium Competition Demo Launcher
color 0A

echo ===================================================
echo 🍄 MYCELIUM NETWORK - COMPETITION BOOTSTRAP 🍄
echo ===================================================
echo.

echo [1/3] Booting Mycelium Registry Server (Port 8000)...
start "Registry Server" cmd /k "python -m server.app"

:: Wait for the server to spin up completely
timeout /t 5 /nobreak >nul

echo [2/3] Spinning up Real-World Agents...
start "RealWeather" cmd /k "python examples/real_agents/real_weather_agent.py"
start "RealTranslator" cmd /k "python examples/real_agents/real_translator_agent.py"
start "CryptoTracker" cmd /k "python examples/real_agents/real_crypto_agent.py"
start "WikiBrain" cmd /k "python examples/real_agents/real_wikipedia_agent.py"
start "CurrencyMaster" cmd /k "python examples/real_agents/real_currency_agent.py"

:: Wait for agents to register
timeout /t 4 /nobreak >nul

echo [3/3] Launching Ideathon Stage UI in Web Browser...
timeout /t 3 /nobreak >nul
start http://127.0.0.1:8000/stage/

echo.
echo ===================================================
echo ✅ ALL SYSTEMS GO! LIVE UI IS OPENING.
echo ===================================================
echo.
echo NOTE: To trigger the automated background chains, run:
echo python scripts/real_world_demo.py
echo.
pause
