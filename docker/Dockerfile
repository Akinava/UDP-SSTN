FROM python:3-alpine
WORKDIR /usr/src/app

# install lib
COPY requirements.txt .
RUN apk add g++
RUN apk add git
RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

# copy app
COPY src/ .
COPY docker/config.json .
COPY docker/shadow .

CMD ["python3", "server.py"]
