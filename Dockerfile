FROM python:3.11-slim

# Install Java
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

EXPOSE 8000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
