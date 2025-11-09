FROM python:3.11-slim

# Installa git
RUN apt-get update && apt-get install -y git

# Copia i file
WORKDIR /app
COPY . /app

# Installa le dipendenze
RUN pip install -r requirements.txt

# Comando di avvio
CMD ["python", "api_server.py"]
