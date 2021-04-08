FROM python:3-alpine
WORKDIR /usr/src/app

# install lib
COPY requirements.txt .
RUN apk add g++
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# copy app
COPY src/ .

CMD ["python3", "server.py"]