from ubuntu:bionic
RUN apt update
RUN apt install -y python python-pip git
RUN python -m pip install tox
RUN mkdir /app
ENV LANG=C.UTF-8
WORKDIR /app
COPY . .
CMD tox
