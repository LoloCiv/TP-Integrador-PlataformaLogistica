FROM python:3.12-slim

# Para que los logs salgan al instante
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Arranca el bucle que escucha Redis
CMD ["python", "main.py"]
