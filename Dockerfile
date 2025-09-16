FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

ENV DJANGO_SETTINGS_MODULE=mysite.settings

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000"]

