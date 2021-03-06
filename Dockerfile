# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY /src /src
COPY /resources /resources
CMD ["python3", "/src/bot.py", "3600", "60"]