FROM python:3.9.7-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD gunicorn backend.wsgi:application --bind 0.0.0.0:8000