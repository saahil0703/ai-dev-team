FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p state meetings docs

EXPOSE 8502

CMD ["python", "run.py", "server"]
