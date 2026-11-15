# Imagen del backend
FROM python:3.12-slim

WORKDIR /code

# Primero las dependencias, así Docker reusa esta capa si no cambiaron
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# En el compose se pisa con --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
