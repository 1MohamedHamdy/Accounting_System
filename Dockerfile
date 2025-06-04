FROM python:3.10-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update && apt-get -y install libpq-dev gcc net-tools curl wget nano

RUN mkdir -p /account_server/logs && chown -R root:root /account_server/logs

WORKDIR /account_server

COPY . /account_server/

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]
