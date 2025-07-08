import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
SECRET = os.environ['SECRET_KEY']

EMAIL_HOST_USER_SECRET = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD_SECRET = os.environ['EMAIL_HOST_PASSWORD']