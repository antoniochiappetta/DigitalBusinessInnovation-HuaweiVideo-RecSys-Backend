# DBI-Backend
Backend services for video streaming application exploiting new recommender system for Huawei Video, made for Digital Business Innovation Lab project @Polimi 2018/19

## Setup

Create the new setup by using a virtual enviroment client such as `python venv` or `virtualenv`.

For instance:

```bash
 $ python -m venv ./venv
```

Activate the environment and install requirements:

```bash
 $ source venv/source/activate
 (venv) $ pip install -r requirements.txt
```

## Run the app

So far there is enough to start the `Flask` server (not recommended for production):

```bash
(venv) $ flask run
```

The `flask` command relies on the `FLASK_APP` environment variable defined in `.flaskenv`.

