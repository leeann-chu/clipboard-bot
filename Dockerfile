FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    bash \
    && apt-get clean 

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "./main.py" ]

