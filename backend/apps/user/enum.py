from django.db.models import TextChoices


class GenderChoices(TextChoices):
    MALE = 'male', 'Мужской'
    FEMALE = 'female', 'Женский'


class PaymentType(TextChoices):
    PREPAID = 'prepaid', 'Предоплата'
    POSTPAID = 'postpaid', 'Постоплата'


class PaymentMethod(TextChoices):
    BY_TRANSFER = ('By transfer to a card after 30 days from the date of order',
                   'Переводом на карту по истечении 30 дней с момента заказа')
    ONLINE = 'Online', 'Онлайн'
    CASH = 'Cash', 'Наличными'
    CARD = 'Card', 'Карта'


class DadataActions(TextChoices):
    CLEAN = ('clean', 'clean')
    SUGGEST = ('suggest', 'suggest')
