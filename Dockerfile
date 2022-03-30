FROM python:3.9-slim-bullseye
COPY . /app
WORKDIR /app
RUN apt-get update
RUN apt-get install -y curl
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
RUN /root/.poetry/bin/poetry install
CMD ["/root/.poetry/bin/poetry", "run", "python", "./main.py"]