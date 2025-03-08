FROM python:3.10.16
WORKDIR /app
COPY . /app
RUN pip3 install --no-deps -r requirements.txt
EXPOSE 500
CMD python ./app.py