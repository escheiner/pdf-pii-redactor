# PDF-PII-Redactor

# Project Setup Instructions

This project uses `fitz` (PyMuPDF) and `spaCy` for PDF processing and natural language processing tasks. Follow the instructions below to set up the environment and install the dependencies.

This has been tested with python3.11 and python3.12 but anything >=3.10 should work. 


If you are familiar with python dependency management, I highly recommend uv by astral (the team that made ruff linter)

## Prerequisites

- Python 3.x installed (Ensure it's a version supported by `fitz` and `spaCy`)
- `pip` (Python package installer)

### Step 1: Clone the repository

```bash
git clone git@github.com:brdhungashi/pdf-pii-redactor.git
cd git@github.com:brdhungashi/pdf-pii-redactor.git
```

### Step 2: Create virtualenv

```
python3 -m venv venv


```


### Step 3: Activate Virtualenv

```
source venv/bin/activate

```


### Step 3: Install Spacy and fitz
In the shell, run:
```
pip install spacy~=3.7.6
pip install pymupdf
```

### Step 4: download spacy en model
In the shell, run:
```
python3 -m spacy download en_core_web_md 
```


### Step 5: Run the redactor
In the shell, run:
```
python3 -m spacy download en_core_web_md 
```


