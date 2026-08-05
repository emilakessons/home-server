FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libcups2-dev \
        cups-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY print_coloring_page.py print_api.py .

CMD ["python", "print_api.py"]
