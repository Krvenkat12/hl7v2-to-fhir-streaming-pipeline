#!/bin/bash

cleanup() {
    echo ""
    echo "=============================================="
    echo "Shutting down processes..."
    echo "=============================================="
    pkill -f "python sender.py"
    pkill -f "python receiver.py"
    pkill -f "streamlit run frontend.py"
    echo "Pipeline processes successfully stopped!"
    exit 0
}

trap cleanup SIGINT

echo "=============================================="
echo "Starting HL7 to FHIR Streaming Pipeline..."
echo "=============================================="

echo "[1/7] Checking for Streamlit Secrets..."
# Check if the secrets file already exists
if [ -f ".streamlit/secrets.toml" ]; then
    echo "Secrets file found!"
else
    if [ ! -d ".streamlit" ]; then
        mkdir .streamlit
    fi
    
    echo ""
    echo "==================================================="
    echo "   GEMINI API KEY REQUIRED FOR AI FEATURES"
    echo "==================================================="
    echo "You need a Google Gemini API key to run the Text-to-SQL bot."
    echo "Get one for free at: https://aistudio.google.com/"

    read -p "Please enter your Gemini API Key: " GEMINI_KEY

    # Writes the key using forward slashes for the actual system path
    echo "GEMINI_API_KEY = \"$GEMINI_KEY\"" > .streamlit/secrets.toml
    # Keeps your exact echo text with the backslash as requested
    echo "Key saved to .streamlit\secrets.toml"
    echo ""
fi

echo "[2/7] Installing dependencies..."
pip install -r requirements.txt

echo "[3/7] Starting Docker services (Kafka, Postgres, HAPI FHIR)..."
docker-compose up -d

echo "[4/7] Allowing 45 seconds for services to initialize..."
sleep 45

echo "[5/7] Opening HAPI FHIR server in your browser..."

if command -v start > /dev/null; then
    start http://localhost:8080/fhir/Patient
elif command -v open > /dev/null; then
    open http://localhost:8080/fhir/Patient
elif command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8080/fhir/Patient
fi

echo "[6/7] Starting the ETL pipeline of sending, transforming, and receiving messages..."
python sender.py &
python receiver.py &

echo "[7/7] Launching Streamlit UI..."
streamlit run frontend.py > dev/null

echo "=============================================="
echo "Pipeline launched successfully!"
echo "=============================================="

wait