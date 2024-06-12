FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y postgresql-client

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app app
COPY application.py .

EXPOSE 5000

CMD [ "python", "application.py"]