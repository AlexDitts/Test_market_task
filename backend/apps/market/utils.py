import datetime
from hashlib import sha256

import pytz
from lxml.etree import Element, SubElement, tostring
from structlog import get_logger

from apps.credentials.models import TinkoffCredentials
from utils.dto import BaseDtoTyping

logger = get_logger(__name__)


def tinkoff_payment__generate_token(
        *, payment_dto: BaseDtoTyping, password: str | None = None
) -> str:
    """
    Требования к генерации токена приведены в документации к API
    https://www.tinkoff.ru/kassa/dev/payments/#section/Parametry-terminala
    """
    if not password:
        password = TinkoffCredentials.get_solo().terminal_pass
    payment_data: dict = payment_dto.dict(exclude_unset=True)
    payment_data["password"] = password
    sortable_keys = {key.lower(): key for key in payment_data.keys()}
    sorted_data: list = sorted(sortable_keys.keys())
    data_list = []
    for key in sorted_data:
        dict_value = payment_data[sortable_keys[key]]
        if not isinstance(dict_value, dict | list):
            data_list.append(str(dict_value))
    concat_str = "".join(data_list)
    import json
    logger.info("tinkoff_payment__generate_token\n" + json.dumps(payment_dto.dict(exclude_unset=True)))
    logger.info("tinkoff_payment__generate_token\n" + concat_str)
    logger.info("tinkoff_payment__generate_token\n" + str(sha256(concat_str.encode("utf-8")).hexdigest()))
    return sha256(concat_str.encode("utf-8")).hexdigest()


def dict_to_xml(d, parent=None, attrib=None):

    if parent is None:
        parent = Element(
            'yml_catalog',
            attrib={'date': datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%dT%H:%M:%S%z")}
        )
    for key, value in d.items():
        if not value:
            continue
        if isinstance(value, dict):
            if value.get('attrib'):
                attrib = value.pop('attrib')
                dict_to_xml(value, SubElement(parent, key, attrib=attrib))
            else:
                dict_to_xml(value, SubElement(parent, key))
        elif isinstance(value, list):
            if key == 'param':
                for item in value:
                    attrib_value, text = item
                    if not text:
                        continue
                    attrib = {'name': str(attrib_value)}
                    SubElement(parent, key, attrib=attrib).text = str(text)
            else:
                child = Element(key)
                parent.append(child)
                for item in value:
                    if not item:
                        continue
                    if item.get('attrib'):
                        attrib = item.pop('attrib')
                    dict_to_xml(item, parent=child, attrib=attrib)
        else:
            SubElement(parent, key, attrib=attrib).text = str(value)
    return parent
