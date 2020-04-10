FROM python:3.7

WORKDIR /usr/src/app

# poetryのインストール
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

# Pythonパッケージのインストール
COPY pyproject.toml poetry.lock ./
RUN export PATH="$HOME/.poetry/bin:$PATH" && \
    poetry export -f requirements.txt > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./main.py" ]