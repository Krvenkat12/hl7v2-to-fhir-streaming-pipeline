@echo off
echo ===================================================
echo   Shutting down program...
echo ===================================================

echo Stopping and removing Docker containers...
docker-compose down

echo ===================================================
echo   Successfully shut down!
echo ===================================================