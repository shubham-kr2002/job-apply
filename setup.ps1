# AI Auto-Applier Agent - Quick Setup Script (Windows PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Auto-Applier Agent - Setup Wizard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "[3/6] Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "[4/6] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel --quiet
Write-Host "✓ Pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "[5/6] Installing dependencies..." -ForegroundColor Yellow
Write-Host "    This may take 2-3 minutes..." -ForegroundColor Gray
pip install --only-binary :all: -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "⚠ Some packages may have issues. Trying alternative method..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Setup environment file
Write-Host ""
Write-Host "[6/6] Setting up environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file from template" -ForegroundColor Green
    Write-Host "⚠ IMPORTANT: Edit .env and add your GROQ_API_KEY" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Get Groq API key from: https://console.groq.com/keys" -ForegroundColor White
Write-Host "  2. Edit .env file and add: GROQ_API_KEY=your_key_here" -ForegroundColor White
Write-Host "  3. Test Phase 1 (Job Discovery):" -ForegroundColor White
Write-Host "     python main.py" -ForegroundColor Cyan
Write-Host "  4. Test Phase 2 (Memory Layer):" -ForegroundColor White
Write-Host "     python memory/brain.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  - README.md (Project overview)" -ForegroundColor White
Write-Host "  - docs/PHASE2_MEMORY.md (RAG system guide)" -ForegroundColor White
Write-Host ""
Write-Host "Happy job hunting! 🎯" -ForegroundColor Green
