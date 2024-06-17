from __future__ import annotations

from zlib import crc32

from moysklad.exceptions import (
    ResponseParseException,
    ApiResponseException,
    RequestFailedException,
    PosTokenException,
)
from moysklad.http.utils import (
    HTTPMethod,
    ApiResponse,
    DEBUG_RATE_HEADERS,
    RequestConfig,
)
from moysklad.queries import Query
from moysklad.urls import ApiUrlRegistry

from json import JSONDecodeError
from time import sleep
from typing import Optional, Union
from urllib.parse import urljoin

from requests import HTTPError, Request, Session
from requests.auth import HTTPBasicAuth


JSON_REQUEST_TYPES = (HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.DELETE)


class MoySkladHttpClient:
    def __init__(
        self,
        login: str,
        password: str,
        pos_token: Optional[str] = None,
        version: str = "1.2",
        pos_version: str = "1.0",
    ) -> None:
        self._login = login
        self._password = password
        self._pos_token = pos_token
        self._pre_request_sleep_time: float = 200
        self._proxies = None

        self._endpoint = f"https://api.moysklad.ru/api/remap/{version}/"
        self._pos_endpoint = f"https://api.moysklad.ru/api/posap/{pos_version}/"

    def set_pos_token(self, pos_token: str) -> None:
        self._pos_token = pos_token

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def pos_endpoint(self):
        return self._pos_endpoint

    def get(
        self,
        method: str,
        data: Union[dict, list] = None,
        query: Optional[Query] = None,
        options: Optional[RequestConfig] = None,
    ):
        return self._make_request(
            http_method=HTTPMethod.GET,
            api_method=method,
            data=data,
            options=options,
            query=query,
        )

    def post(
        self,
        method: str,
        data: Union[dict, list] = None,
        query: Optional[Query] = None,
        options: Optional[RequestConfig] = None,
    ):
        return self._make_request(
            http_method=HTTPMethod.POST,
            api_method=method,
            data=data,
            options=options,
            query=query,
        )

    def put(
        self,
        method: str,
        data: Union[dict, list] = None,
        query: Optional[Query] = None,
        options: Optional[RequestConfig] = None,
    ):
        return self._make_request(
            http_method=HTTPMethod.PUT,
            api_method=method,
            data=data,
            options=options,
            query=query,
        )

    def delete(
        self,
        method: str,
        data: Union[dict, list] = None,
        query: Optional[Query] = None,
        options: Optional[RequestConfig] = None,
    ):
        return self._make_request(
            http_method=HTTPMethod.DELETE,
            api_method=method,
            data=data,
            options=options,
            query=query,
        )

    def set_pre_request_timeout(self, ms: float) -> None:
        self._pre_request_sleep_time = ms

    def set_proxies(self, proxies: Optional[dict]):
        self._proxies = proxies

    # pylint: disable-msg=too-many-locals
    def _make_request(
        self,
        http_method: HTTPMethod,
        api_method: str,
        data: Optional[Union[dict, list]] = None,
        options: Optional[RequestConfig] = None,
        **kwargs,
    ):
        if not data:
            data = {}
        if not options:
            options = RequestConfig()

        password = self._password
        endpoint = self._endpoint

        if options.use_pos_api:
            if options.use_pos_token:
                if not self._pos_token:
                    raise PosTokenException(
                        "POS token is used, but it's invalid or empty"
                    )
                password = self._pos_token
            endpoint = self._pos_endpoint

        auth = HTTPBasicAuth(self._login, password)

        headers = {}
        if options.format_millisecond:
            headers["X-Lognex-Format-Millisecond"] = "true"
        if options.disable_webhooks_dispatch:
            headers["X-Lognex-WebHook-Disable"] = "true"
        if options.debug_rate_limit:
            headers.update(DEBUG_RATE_HEADERS)
        if options.custom_headers:
            headers.update(options.custom_headers)

        query = kwargs.get("query") or Query()
        request_payload = {
            "method": http_method.value,
            "url": urljoin(endpoint, api_method),
            "headers": headers,
            "auth": auth,
            "params": query.url_params,
        }

        if not options.ignore_request_body:
            if http_method == HTTPMethod.GET and isinstance(data, dict):
                request_payload["params"].update(data)
            elif http_method in JSON_REQUEST_TYPES:
                request_payload["json"] = data
            else:
                raise NotImplementedError("Unsupported request type")

        session = Session()
        request = Request(**request_payload)
        prepared = session.prepare_request(request)

        try:
            sleep(self._pre_request_sleep_time / 1000)

            res = session.send(
                request=prepared,
                allow_redirects=options.follow_redirects,
                proxies=self._proxies,
            )
            res.raise_for_status()
        except HTTPError as exc:
            res = exc.response
            e = RequestFailedException(res)

            try:
                res_json = res.json()
                is_list = isinstance(res_json, list)
                errors = (
                    res_json[0].get("errors") if is_list else res_json.get("errors")
                )
                if errors:
                    e = ApiResponseException(res, errors)
            except JSONDecodeError:
                pass
            finally:
                raise e from exc

        if http_method == HTTPMethod.DELETE:
            return None

        if not options.follow_redirects and res.is_redirect:
            return res.headers.get("location", "")

        try:
            json_response = res.json()
            return ApiResponse(res, json_response)
        except JSONDecodeError as exc:
            if res.headers["Content-Type"] == "application/octet-stream":
                return res
            raise ResponseParseException(exc, res)


class MoySklad:
    _instances: dict = {}

    def __init__(
        self, login: str, password: str, pos_token: str, hash_code: str
    ) -> None:
        self._client = MoySkladHttpClient(login, password, pos_token)
        self._methods = ApiUrlRegistry()
        self._hash_code = hash_code

    @classmethod
    def get_instance(
        cls, login: str, password: str, pos_token: Optional[str] = None
    ) -> MoySklad:
        hash_code = crc32(f"{login}{password}".encode()) & 0xFFFFFFFF
        if not cls._instances.get(hash_code):
            cls._instances[hash_code] = cls(
                login=login,
                password=password,
                pos_token=pos_token,
                hash_code=hash_code,
            )
        return cls._instances[hash_code]

    @classmethod
    def find_instance_by_hash(cls, hash_code: str) -> MoySklad:
        return cls._instances.get(hash_code)

    @property
    def hash_code(self) -> str:
        return self._hash_code

    def get_client(self) -> MoySkladHttpClient:
        return self._client

    def get_methods(self) -> ApiUrlRegistry:
        return self._methods

    def set_pos_token(self, pos_token) -> None:
        self._client.set_pos_token(pos_token)
