from configurations.values import BooleanValue, Value, IntegerValue

from config.settings.base import Base


class Development(Base):
    DEBUG = BooleanValue(True)
    DOMAIN = Value('https://gksport.bulltech.ru')
    EMAIL_HOST = Value("smtp.yandex.ru")
    EMAIL_PORT = IntegerValue(587)
    EMAIL_HOST_USER = Value()
    EMAIL_HOST_PASSWORD = Value()
    EMAIL_USE_TLS = BooleanValue(True)
    EMAIL_USE_SSL = BooleanValue(False)
    SERVER_EMAIL = EMAIL_HOST_USER
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
    RECIPIENTS_EMAIL = ""

