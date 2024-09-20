FROM python:3.12-slim
RUN apt update
RUN apt install -y build-essential
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN pip install pymupdf
RUN pip install spacy
RUN python3 -m spacy download en_core_web_md
COPY . /app
WORKDIR /app
# pip install -U pip setuptools wheel
# pip install -U 'spacy[apple]'
