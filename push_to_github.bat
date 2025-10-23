@echo off
echo.
echo ========================================
echo   PUSHING TO GITHUB
echo ========================================
echo.

REM Replace these with your actual GitHub details
set GITHUB_USERNAME=XerxesNagato
set REPO_NAME=DzKeyz

echo Adding GitHub remote...
git remote add origin https://github.com/XerxesNagato/DzKeyz.git

echo.
echo Setting main branch...
git branch -M main

echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo   SUCCESS! Your code is now on GitHub
echo ========================================
echo.
echo Repository URL: https://github.com/XerxesNagato/DzKeyz.git
echo.
pause