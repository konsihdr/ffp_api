# Verwende das offizielle Python-Image als Basis
FROM python:3.11-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die Abhängigkeiten in das Arbeitsverzeichnis
COPY . .

# Installiere die Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Starte die Anwendung mit Gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "wsgi:app"]