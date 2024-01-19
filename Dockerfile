FROM python:3.11-slim

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip install gunicorn

COPY flaskapp flaskapp
COPY migrations migrations
COPY app.py config.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENV FLASK_APP app.py

EXPOSE 5000
ENTRYPOINT ["./entrypoint.sh"]