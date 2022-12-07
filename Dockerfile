FROM python:3.10
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH "${PYTHONPATH}:/mycode"
WORKDIR /mycode
COPY requirements.txt /mycode/
RUN pip install -r requirements.txt
COPY ./src/ /mycode/
