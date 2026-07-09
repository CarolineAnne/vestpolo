"""
Django settings for core project.
"""

from pathlib import Path
import os
import dj_database_url
from decouple import config
import cloudinary
import cloudinary_storage

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-1+p!vn6u7*4gerak&lkf=gm)yt91tfg3e-^gh71k$p59$i27nw'
)

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.onrender.com']

CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'cloudinary',

    'loja',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET'),
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = f'VestPolo <{EMAIL_HOST_USER}>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL


# Melhor Envio
MELHOR_ENVIO_BASE_URL = config(
    'MELHOR_ENVIO_BASE_URL',
    default='https://sandbox.melhorenvio.com.br'
)

MELHOR_ENVIO_TOKEN = config(
    'MELHOR_ENVIO_TOKEN',
    default=''
)

MELHOR_ENVIO_CLIENT_ID = config(
    'MELHOR_ENVIO_CLIENT_ID',
    default=''
)

MELHOR_ENVIO_CLIENT_SECRET = config(
    'MELHOR_ENVIO_CLIENT_SECRET',
    default=''
)

MELHOR_ENVIO_CEP_ORIGEM = config(
    'MELHOR_ENVIO_CEP_ORIGEM',
    default='48913126'
)

MELHOR_ENVIO_PESO = config(
    'MELHOR_ENVIO_PESO',
    default=0.35,
    cast=float
)

MELHOR_ENVIO_COMPRIMENTO = config(
    'MELHOR_ENVIO_COMPRIMENTO',
    default=30,
    cast=int
)

MELHOR_ENVIO_LARGURA = config(
    'MELHOR_ENVIO_LARGURA',
    default=25,
    cast=int
)

MELHOR_ENVIO_ALTURA = config(
    'MELHOR_ENVIO_ALTURA',
    default=5,
    cast=int
)

MELHOR_ENVIO_USER_AGENT = config(
    'MELHOR_ENVIO_USER_AGENT',
    default='VestPolo - vestpolopolos@gmail.com'
)


# Pagamentos
PIX_CHAVE = config('PIX_CHAVE', default='')
PIX_NOME_RECEBEDOR = config('PIX_NOME_RECEBEDOR', default='VESTPOLO')
PIX_CIDADE_RECEBEDOR = config('PIX_CIDADE_RECEBEDOR', default='PETROLINA')

MERCADO_PAGO_ACCESS_TOKEN = config('MERCADO_PAGO_ACCESS_TOKEN', default='')
