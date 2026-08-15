FROM python:3.14.6-slim

ENV PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/config/config.ini

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY assembler.py config.py data.py error.py file.py main.py parser.py requester.py ./

RUN mkdir -p /config /data
WORKDIR /data

CMD ["python", "/app/main.py"]
