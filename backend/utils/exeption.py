from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.exceptions import APIException


class BadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Есть ошибки в формировании запроса.'
    default_code = 'bad_request'


class BusinessLogicException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Что-то пошло не так, обратитесь в поддержку.'
    default_code = 'business_logic_error'


def render404(*, request: WSGIRequest) -> HttpResponse:
    return render(
        request,
        '404.html'
    )
