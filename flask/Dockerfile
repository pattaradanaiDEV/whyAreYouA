# pull official base image
FROM python:3.10-alpine3.17


# This prevents Python from writing out pyc files
ENV PYTHONDONTWRITEBYTECODE 1


# This keeps Python from buffering stdin/stdout
ENV PYTHONUNBUFFERED 1


# set work directory
WORKDIR /flask_app

# ตั้งค่า timezone
ENV TZ=Asia/Bangkok
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# update the system and add git
RUN apk update && apk --no-cache add \
    git \
    gcc \
    libc-dev \
    libffi-dev \
    pango-dev \
    cairo-dev \
    gdk-pixbuf-dev \
    glib-dev \
    fontconfig \
    ttf-dejavu


# install dependencies
COPY ./requirements.txt /flask_app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt


# copy project
COPY . /flask_app


# specify the entry point
ENTRYPOINT [ "./gunicorn_starter.sh" ]


# keep the Docker process running even when crashes
CMD ["tail", "-f", "/dev/null"]
