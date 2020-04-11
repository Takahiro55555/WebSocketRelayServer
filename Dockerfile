FROM python:3.7

# nginxのインストール
RUN wget https://nginx.org/keys/nginx_signing.key && \
    apt-key add nginx_signing.key && \
    rm nginx_signing.key && \
    echo "deb http://nginx.org/packages/debian/ buster nginx" >> /etc/apt/sources.list && \
    echo "deb-src http://nginx.org/packages/debian/ buster nginx" >> /etc/apt/sources.list && \
    apt update && \
    apt -y install nginx

WORKDIR /usr/src/app

# poetryのインストール
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

# Pythonパッケージのインストール
COPY pyproject.toml poetry.lock ./
RUN export PATH="$HOME/.poetry/bin:$PATH" && \
    poetry export -f requirements.txt > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

RUN echo "#!/usr/bin/env bash" >> /startup.sh && \
    echo "service nginx start" >> /startup.sh && \
    echo "python ./main.py" >> /startup.sh && \
    chmod +x /startup.sh
CMD ["/startup.sh"]