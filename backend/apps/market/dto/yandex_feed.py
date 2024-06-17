import datetime

from pydantic import BaseModel


class OfferDto(BaseModel):
    vendor: str
    vendor_code: str
    url: str
    price: float
    old_price: float
    enable_auto_discounts: bool = True
    currency_ID: str = 'ROR'
    category_ID: str
    picture: str
    description: str
    sales_notes: str
    manufacturer_warranty: str
    barcode: str
    param: str
    weight: float
    dimensions: str


class CategoryDto(BaseModel):
    id: str
    name: str


class WrapCategoryDto(BaseModel):
    category: CategoryDto


class WrapOfferDto(BaseModel):
    offer: OfferDto


class ShopYandexFeedDto(BaseModel):
    platform: str = 'GKSport'
    name: str = 'GKSport'
    company: str = 'GKSport'
    url: str = 'https://www.gksport.ru'
    categories: list[WrapCategoryDto] = []
    offers: list[WrapOfferDto] = []


class YandexFeedFileDto(BaseModel):
    yml_catalog_date: str = datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')
