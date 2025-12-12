# Use the same Python version as your .venv (replace 3.11 with your version if needed)
FROM python:3.11-slim

WORKDIR /app

COPY src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

EXPOSE 5000

CMD ["python", "app.py"]
