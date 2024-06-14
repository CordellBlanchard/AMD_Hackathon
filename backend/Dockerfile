FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y postgresql-client iputils-ping curl wget ca-certificates && \ 
    update-ca-certificates

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app app
COPY application.py .    

# REMOVE THESE 3 LINES IF NOT ON AMD LAPTOP/NETWORK
COPY AMD_CA.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates 
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

EXPOSE 5000

CMD [ "python", "application.py"]