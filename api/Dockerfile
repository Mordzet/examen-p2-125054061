FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar cliente SSH para permitir conexión hacia el contenedor hadoop (ssh usuario@hadoop)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /root/.ssh /ssh_shared \
    && printf "Host *\n    StrictHostKeyChecking no\n    UserKnownHostsFile /dev/null\n    IdentityFile /ssh_shared/id_rsa\n    LogLevel ERROR\n" >> /etc/ssh/ssh_config

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]

