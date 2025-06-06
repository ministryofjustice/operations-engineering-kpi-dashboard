FROM python:3.12.8-slim-bookworm

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y perl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

LABEL maintainer="operations-engineering <operations-engineering@digital.justice.gov.uk>"

RUN groupadd -r user && useradd -r -g user 1051

WORKDIR /home/operations-engineering-kpi-dashboard

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
COPY app app
COPY example-data data
COPY data/production production

RUN pip3 install --no-cache-dir pipenv==2024.4.0 && \
  pipenv install --system --deploy --ignore-pipfile

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 4567

USER 1051

ENTRYPOINT ["gunicorn", "--bind=0.0.0.0:4567", "app.run:app()"]
