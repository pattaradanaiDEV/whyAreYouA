#!/bin/sh
if [ "$FLASK_DEBUG" = "1" ]; then
    echo "Running on Flask Development Server"
    cd app || exit 1    
    python3 ../main.py
else
    echo "Running on gunicorn"
    gunicorn main:app -c "$PWD"/gunicorn.config.py
fi
exec "$@"
