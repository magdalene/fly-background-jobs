FROM --platform=amd64 python:3.11

ADD requirements.txt /tmp

RUN pip install -r /tmp/requirements.txt

RUN rm /tmp/requirements.txt

ADD *.py /code/

WORKDIR /code/

CMD ["python", "worker.py"]