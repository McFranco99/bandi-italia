FROM python:3.11-slim

# Installa git
RUN apt-get update && apt-get install -y git

# Copia i file
WORKDIR /app
COPY . /app

# Installa le dipendenze
RUN pip install -r requirements.txt

# Comando di avvio
CMD ["bash", "-c", "gunicorn -b 0.0.0.0:${PORT:-5000} api_server:app"]


