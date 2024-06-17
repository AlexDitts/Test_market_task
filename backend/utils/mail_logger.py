from django.core.mail import send_mail


def mail_logger(message):
    send_mail(
                subject='Log',
                from_email='ditts@bulltech.ru',
                auth_user='ditts@bulltech.ru',
                auth_password='lzqnlqmpxriqmdcl',
                message=message,
                recipient_list=['ahil78@yandex.ru']
)
