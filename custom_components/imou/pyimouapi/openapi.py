import hashlib
import json
import logging
import secrets
import time
import uuid

import aiohttp
import async_timeout

from .const import API_ENDPOINT_ACCESS_TOKEN, ERROR_CODE_INVALID_APP, \
    ERROR_CODE_INVALID_SIGN, \
    ERROR_CODE_SUCCESS, ERROR_CODE_TOKEN_OVERDUE, PARAM_ACCESS_TOKEN, PARAM_SYSTEM, PARAM_VER, PARAM_SIGN, PARAM_APP_ID, \
    PARAM_TIME, PARAM_NONCE, PARAM_PARAMS, PARAM_ID, PARAM_RESULT, PARAM_DATA, PARAM_CODE, PARAM_TOKEN, PARAM_MSG
from .exceptions import ConnectFailedException, RequestFailedException, \
    InvalidAppIdOrSecretException

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ImouOpenApiClient:

    def __init__(self, app_id: str, app_secret: str, api_url: str) -> None:
        self._app_id = app_id
        self._app_secret = app_secret
        self._api_url = api_url
        # token
        self._access_token = None

    async def async_get_token(self) -> None:
        """get accessToken"""
        response = await self.async_request_api(API_ENDPOINT_ACCESS_TOKEN, {})
        self._access_token = response[PARAM_ACCESS_TOKEN]

    async def async_request_api(self, endpoint: str, params: dict[any, any] = None) -> dict[any, any]:
        # if accessToken is None , get first
        if self._access_token is None and endpoint != API_ENDPOINT_ACCESS_TOKEN:
            await self.async_get_token()
        params[PARAM_TOKEN] = self._access_token
        timestamp = round(time.time())
        nonce = secrets.token_urlsafe()
        sign = hashlib.md5(f"time:{timestamp},nonce:{nonce},appSecret:{self._app_secret}".encode("utf-8")).hexdigest()
        request_id = str(uuid.uuid4())
        headers = {
            "Content-Type": "application/json",
            "Client-Type": "HomeAssistant"
        }
        body = {
            PARAM_SYSTEM: {
                PARAM_VER: "1.0",
                PARAM_SIGN: sign,
                PARAM_APP_ID: self._app_id,
                PARAM_TIME: timestamp,
                PARAM_NONCE: nonce,
            },
            PARAM_PARAMS: params,
            PARAM_ID: request_id,
        }
        url = f"https://{self._api_url}{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(30):
                    response = await session.request("POST", url, json=body, headers=headers)
                    response_body = json.loads(await response.text())
                    _LOGGER.info(f"url: {url} request body: {body} response: {response_body}")
        except Exception as exception:
            raise ConnectFailedException(f"connect failed,{exception}") from exception
        if response.status != 200:
            raise RequestFailedException(f"request failed,status code {response.status}")
        result_code = response_body[PARAM_RESULT][PARAM_CODE]
        result_message = response_body[PARAM_RESULT][PARAM_MSG]
        if result_code != ERROR_CODE_SUCCESS:
            msg = result_code + ":" + result_message
            if result_code in (ERROR_CODE_INVALID_SIGN, ERROR_CODE_INVALID_APP):
                raise InvalidAppIdOrSecretException(msg)
            if result_code == ERROR_CODE_TOKEN_OVERDUE:
                await self.async_get_token()
                return await self.async_request_api(endpoint, params)
            raise RequestFailedException(msg)
        response_data = response_body[PARAM_RESULT][PARAM_DATA] if PARAM_DATA in response_body[PARAM_RESULT] else {}
        return response_data

    @property
    def access_token(self):
        return self._access_token
