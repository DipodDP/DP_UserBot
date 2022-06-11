FROM python
ENV BOT_NAME=$BOT_NAME

WORKDIR /app

COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt
COPY . /app

CMD ["python", "/app/Get_ID.py"]