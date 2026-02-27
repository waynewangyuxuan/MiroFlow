# MiroFlow Code Execution Sandbox
# Pre-built image with scientific computing packages for agent code execution.
#
# Build:  docker build -t miroflow-sandbox sandbox/
# Test:   docker run --rm miroflow-sandbox python -c "import numpy; print(numpy.__version__)"

FROM python:3.12-slim

# ── System packages ──────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    pdfgrep \
    libimage-exiftool-perl \
    stockfish \
    wget \
    curl \
    git \
    ffmpeg \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# ── Python packages (split into layers for cache efficiency) ─────────────────
# Core scientific stack (changes rarely)
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scipy \
    matplotlib \
    sympy \
    scikit-learn

# Domain-specific packages
RUN pip install --no-cache-dir \
    PyPDF2 \
    PyMuPDF \
    pdfminer.six \
    pdfplumber \
    python-pptx \
    python-docx \
    docx2txt \
    openpyxl

RUN pip install --no-cache-dir \
    geopy \
    geopandas \
    pyshp \
    networkx \
    seaborn \
    Pillow \
    opencv-python-headless

RUN pip install --no-cache-dir \
    biopython \
    pubchempy \
    CoolProp \
    yfinance \
    wbdata

RUN pip install --no-cache-dir \
    python-chess \
    stockfish \
    pytesseract \
    SpeechRecognition \
    pydub \
    yt-dlp \
    waybackpy \
    googletrans==4.0.0-rc1 \
    requests

# ── Workspace ────────────────────────────────────────────────────────────────
RUN useradd -m -s /bin/bash sandbox
WORKDIR /home/sandbox
USER sandbox

CMD ["sleep", "infinity"]
