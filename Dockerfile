FROM python:3-alpine

EXPOSE 5002

WORKDIR .

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python","launch_app.py"]
