
from .base import *

DEBUG = True
hostname = socket.gethostname()
host_ip = socket.gethostbyname(hostname)
ALLOWED_HOSTS = ['localhost',"10.10.8.115","calibr8.ddns.net",host_ip]

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # }
    'default': {
        'ENGINE': "django.db.backends.postgresql_psycopg2",
        'NAME': "JIMAHCERT",
        'USER': "jimah-cert-admin",
        'PASSWORD': "C8@dm1n",
        'HOST': "localhost",
        'PORT': "5432",
    }
}
