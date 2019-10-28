FROM python:3-alpine

WORKDIR .

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python","launch_app.py"]