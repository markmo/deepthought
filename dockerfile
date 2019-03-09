# base image
FROM python:3.6.8-slim

# install netcat
RUN apt-get update && \
    apt-get -y install netcat git gcc && \
    apt-get clean

WORKDIR /usr/src
RUN git clone https://github.com/facebookresearch/DrQA.git
WORKDIR /usr/src/DrQA
RUN pip install -r requirements.txt && \
    python setup.py develop

# set working directory
WORKDIR /usr/src/app

# add and install requirements
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt
RUN pip install https://download.pytorch.org/whl/cpu/torch-1.0.1.post2-cp36-cp36m-linux_x86_64.whl
RUN pip install torchvision

# add entrypoint.sh
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# make directories
RUN mkdir database
RUN mkdir model

# add app
COPY ./database/legal.db /usr/src/app/database/
COPY ./model/legal-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz /usr/src/app/model/
COPY ./app.py /usr/src/app
COPY ./tasks.py /usr/src/app
COPY ./util.py /usr/src/app
COPY ./wsgi.py /usr/src/app

# run server
CMD ["/usr/src/app/entrypoint.sh"]
