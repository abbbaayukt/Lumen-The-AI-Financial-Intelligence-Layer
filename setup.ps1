# PowerShell script to setup the Lumen project

Write-Output "--- Setting up Lumen Project ---"

# Setup Backend
Write-Output "`n[1/3] Setting up Backend..."
Set-Location -Path "backend"

if (-not (Test-Path ".venv")) {
    Write-Output "Creating virtual environment..."
    python -m venv .venv
}

Write-Output "Installing backend dependencies..."
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Output "Creating .env file from .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Output "IMPORTANT: Please update the API keys in backend/.env"
}

Set-Location -Path ".."

# Setup Frontend
Write-Output "`n[2/3] Setting up Frontend..."
Set-Location -Path "frontend"

if (-not (Test-Path "node_modules")) {
    Write-Output "Installing frontend dependencies..."
    npm install
}

Set-Location -Path ".."

Write-Output "`n[3/3] Setup Complete!"
Write-Output "You can now run the project using run.bat or run.ps1"
Write-Output "--------------------------------"
