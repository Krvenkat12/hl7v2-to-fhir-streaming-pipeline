@echo off
echo ==============================================
echo Starting HL7 to FHIR Streaming Pipeline...
echo ==============================================

echo [1/7] Checking for Streamlit Secrets...
:: Check if the secrets file already exists
if exist ".streamlit\secrets.toml" (
    echo Secrets file found!
) else (
    if not exist ".streamlit" mkdir .streamlit
    
    echo.
    echo ===================================================
    echo   GEMINI API KEY REQUIRED FOR AI FEATURES
    echo ===================================================
    echo You need a Google Gemini API key to run the Text-to-SQL bot.
    echo Get one for free at: https://aistudio.google.com/

    set /p GEMINI_KEY="Please enter your Gemini API Key: "

    echo GEMINI_API_KEY = "%GEMINI_KEY%" > .streamlit\secrets.toml
    echo Key saved to .streamlit\secrets.toml
    echo.
)

echo [2/7] Installing dependencies...
pip install -r requirements.txt

echo [3/7] Starting Docker services (Kafka, Postgres, HAPI FHIR)...
docker-compose up -d

echo [4/7] Allowing 15 seconds for services to initialize...
timeout /t 15 /nobreak > NUL

echo [5/7] Opening HAPI FHIR server in your browser...
start http://localhost:8080/fhir/Patient

echo [6/7] Starting the ETL pipeline of sending, transforming, and receiving messages...
start cmd /k "title Sender & python sender.py"
start cmd /k "title Receiver & python receiver.py"

echo [7/7] Launching Streamlit UI...
start cmd /k "title Streamlit App & python -m streamlit run frontend.py"

echo ==============================================
echo Pipeline launched successfully!
echo ==============================================