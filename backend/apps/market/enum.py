from django.db.models import TextChoices


class BasketStatus(TextChoices):
    IS_ACTIVE = 'is_active', 'активно'
    UNACCEPTED = 'unaccepted', 'снято с резервации'
    COMPLETED = 'complete', 'оформлен'


class PaymentStatus(TextChoices):
    PAID = 'paid', 'оплачен' #check_payment
    UNPAID = 'UNPAID', 'не оплачен' #accept
    AWAITING_PAYMENT = 'awaiting_payment', 'ожидает оплаты'  #create_payment


class PaymentMethod(TextChoices):
    ONLINE = 'online', 'Онлайн'
    ON_RECEIPT_CARD = 'on_receipt_card', 'Картой при получении'
    ON_RECEIPT_CASH = 'on_receipt_cash', 'Наличными при получении'
    KORONAPAY = 'koronapay', 'Золотая корона'
    LEGAL = 'legal', 'Договор для юридических лиц'


class ShippingMethod(TextChoices):
    CUSTOM = 'custom', 'Настраиваемый способ доставки'
    PICKUP = 'pickup', 'Самовывоз'
    COURIER = 'courier', 'Курьерская'
    CDEK_136 = 'cdek-136', 'СДЭК-136'
    CDEK_137 = 'cdek-137', 'СДЭК-137'
    CDEK_233 = 'cdek-233', 'СДЭК-233'
    CDEK_234 = 'cdek-234', 'СДЭК-234'
    CDEK_482 = 'cdek-482', 'СДЭК-482'
    CDEK_483 = 'cdek-483', 'СДЭК-483'


class WeekDays(TextChoices):
    MONDAY = '0', 'Понедельник'
    TUESDAY = '1', 'Вторник'
    WEDNESDAY = '2', 'Среда'
    THURSDAY = '3', 'Четверг'
    FRIDAY = '4', 'Пятница'
    SATURDAY = '5', 'Суббота'
    SUNDAY = '6', 'Воскресенье'


class OrderStatus(TextChoices):
    ORDERED = 'ordered', 'заказан'


class ColorSample(TextChoices):
    WHITE = "#000000", "Черный"
    BLACK = "#FFFFFF", "Белый"
    RED = "#FF0000", "Красный"
    GREEN = "#00FF00", "Зеленый"
    BLUE = "#0000FF", "Синий"
    YELLOW = "#FFFF00", "Желтый"
    PINK = "#FFC0CB", "Розовый"
    ORANGE = "#FFA500", "Оранжевый"
    PURPLE = "#800080", "Фиолетовый"
    CYAN = "#00FFFF", "Голубой"


class TypeLabel(TextChoices):
    PROMOTION = 'promotion', 'Скидка'
    NEW = 'new', 'Новинка'
    BESTSELLER = 'bestseller', 'Хит'
    CUSTOM = 'custom', 'Пользовательский'
