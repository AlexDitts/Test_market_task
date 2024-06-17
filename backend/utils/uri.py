from urllib.parse import urlparse


def protocol_with_domain_uri__convert(*, absolute_uri: str) -> str:
    """
    Принимает абсолютный путь в формате - http://localhost:8000/api/basket_sets_of_packages/1/?param=1
    Возвращает ссылку с протоколом и доменом в формате: http://localhost:8000
    """
    url_parsed_data = urlparse(absolute_uri)
    protocol = "https"
    domain = url_parsed_data.netloc
    return f"{protocol}://{domain}"
