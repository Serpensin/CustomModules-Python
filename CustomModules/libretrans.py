import asyncio
import logging
from typing import Optional

import aiofiles
import aiohttp


class Errors:
    class InvalidAPIKey(Exception):
        def __init__(self, message="Invalid API key or URL."):
            super().__init__(message)

    class BadRequest(Exception):
        def __init__(self, message="Bad Request: The request was invalid."):
            super().__init__(message)

    class Forbidden(Exception):
        def __init__(
            self,
            message="Forbidden: The API key is invalid or the request is not authorized.",
        ):
            super().__init__(message)

    class RateLimitExceeded(Exception):
        def __init__(
            self, message="Rate Limit Exceeded: The request was rate limited."
        ):
            super().__init__(message)

    class InternalServerError(Exception):
        def __init__(
            self, message="Internal Server Error: The server encountered an error."
        ):
            super().__init__(message)


class API:
    """
    Class for interacting with a translation API asynchronously using aiohttp.
    """

    def __init__(self, api_key, url, logger: Optional[logging.Logger] = None):
        """
        Initialize the API object.

        Args:
            api_key (str): The API key for accessing the translation API.
            url (str): The base URL of the translation API.
            logger (Optional[logging.Logger]): Parent logger. If provided, creates a child logger
            under CustomModules.Libretrans. Defaults to None.

        Raises:
            Errors.InvalidAPIKey: If the provided API key is invalid.
        """
        # Setup logger with child hierarchy: parent -> CustomModules -> Libretrans
        if logger:
            self.logger = logger.getChild("CustomModules").getChild("Libretrans")
        else:
            self.logger = logging.getLogger("CustomModules.Libretrans")

        self.logger.debug(f"Initializing Libretrans API with URL: {url}")

        self.api_key = api_key
        self.url = url.rstrip("/")
        if not asyncio.run(self.validate_key()):
            self.logger.error("API key validation failed")
            raise Errors.InvalidAPIKey()

        self.logger.info("Libretrans API initialized successfully")

    async def _get_sample(self, text: str, is_file: bool = False) -> str:
        """
        Extract a sample text from either a string or a file.

        Args:
            text (str): The input text or path to the file.
            is_file (bool): Indicates whether the input is a file path.

        Returns:
            str: The sample text.
        """
        if is_file:
            async with aiofiles.open(text, "r", encoding="utf-8") as file:
                text = await file.read()

        first_words = text.split(" ")
        return " ".join(first_words[:20])

    async def detect(self, text: str) -> dict:
        """
        Asynchronously detect the language of a given text.

        Args:
            text (str): The input text to detect language.

        Returns:
            dict: A dictionary containing the HTTP response status and detected language data.

        Raises:
            Errors.BadRequest: If the request is invalid.
            Errors.Forbidden: If the API key is invalid or the request is not authorized.
            Errors.RateLimitExceeded: If the request was rate limited.
            Errors.InternalServerError: If the server encountered an error.
            Errors.InvalidAPIKey: If the URL is invalid or unable to connect to the server.
        """
        self.logger.debug("Detecting language for text sample")
        url = f"{self.url}/detect"
        params = {"q": text, "api_key": self.api_key}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, params=params) as response:
                    data = await response.json()
                    response_data = {"status": response.status, "data": data}
                    if response.status == 200:
                        detected_lang = data[0]["language"] if data else "unknown"
                        self.logger.info(f"Detected language: {detected_lang}")
                        return response_data
                    elif response.status == 400:
                        self.logger.error(
                            f"Bad request during language detection: {data}"
                        )
                        raise Errors.BadRequest(str(response_data))
                    elif response.status == 403:
                        self.logger.error(
                            f"Forbidden during language detection: {data}"
                        )
                        raise Errors.Forbidden(str(response_data))
                    elif response.status == 429:
                        self.logger.warning(
                            f"Rate limit during language detection: {data}"
                        )
                        raise Errors.RateLimitExceeded(str(response_data))
                    elif response.status == 500:
                        self.logger.error("Server error during language detection")
                        raise Errors.InternalServerError(str(response_data))
                    else:
                        self.logger.error(f"Unexpected status code: {response.status}")
                        raise Errors.BadRequest(str(response_data))
            except aiohttp.ClientConnectorDNSError:
                self.logger.error("DNS error - invalid URL or unable to connect")
                raise Errors.InvalidAPIKey(
                    "Invalid URL or unable to connect to the server."
                )

    async def translate_text(self, text: str, dest_lang: str, source: str = "") -> str:
        """
        Asynchronously translate a given text to the specified destination language.

        Args:
            text (str): The input text to translate.
            dest_lang (str): The destination language code.
            source (str, optional): The source language code. Defaults to ''.

        Returns:
            str: The translated text.

        Raises:
            Errors.BadRequest: If the request is invalid.
            Errors.Forbidden: If the API key is invalid or the request is not authorized.
            Errors.RateLimitExceeded: If the request was rate limited.
            Errors.InternalServerError: If the server encountered an error.
        """
        self.logger.debug(
            f"Translating text to {dest_lang} (source: {source or 'auto'})"
        )
        url = f"{self.url}/translate"
        if not source:
            detected = await self.detect(await self._get_sample(text))
            source = detected["data"][0]["language"]
            self.logger.debug(f"Detected source language: {source}")
        params = {
            "q": text,
            "source": source,
            "target": dest_lang,
            "api_key": self.api_key,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                data = await response.json()
                if response.status == 200:
                    self.logger.info(
                        f"Successfully translated text from {source} to {dest_lang}"
                    )
                    return data["translatedText"]
                elif response.status == 400:
                    self.logger.error(f"Bad request error: {data}")
                    raise Errors.BadRequest(str(data))
                elif response.status == 403:
                    self.logger.error(f"Forbidden error: {data}")
                    raise Errors.Forbidden(str(data))
                elif response.status == 429:
                    self.logger.warning(f"Rate limit exceeded: {data}")
                    raise Errors.RateLimitExceeded(str(data))
                elif response.status == 500:
                    self.logger.error(f"Server error: {data}")
                    raise Errors.InternalServerError(str(data))
                else:
                    self.logger.error(f"Unexpected status code: {response.status}")
                    raise Errors.BadRequest(str(data))

    async def translate_file(self, file: str, dest_lang: str, source: str = "") -> str:
        """
        Asynchronously translate the content of a file to the specified destination language.

        Args:
            file (str): The path to the file to translate.
            dest_lang (str): The destination language code.
            source (str, optional): The source language code. Defaults to ''.

        Returns:
            str: The URL of the translated file.

        Raises:
            Errors.BadRequest: If the request is invalid.
            Errors.Forbidden: If the API key is invalid or the request is not authorized.
            Errors.RateLimitExceeded: If the request was rate limited.
            Errors.InternalServerError: If the server encountered an error.
        """
        self.logger.debug(
            f"Translating file to {dest_lang} (source: {source or 'auto'})"
        )
        url = f"{self.url}/translate_file"
        if not source:
            source = (await self.detect(await self._get_sample(file, True)))["data"][0][
                "language"
            ]
            self.logger.debug(f"Detected file language: {source}")
        form = aiohttp.FormData()
        form.add_field("source", source)
        form.add_field("target", dest_lang)
        form.add_field("api_key", self.api_key)
        async with aiofiles.open(file, "rb") as f:
            file_content = await f.read()
            form.add_field(
                "file",
                file_content,
                filename=file,
                content_type="application/octet-stream",
            )
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form) as response:
                    data = await response.json()
                    if response.status == 200:
                        self.logger.info(
                            f"Successfully translated file from {source} to {dest_lang}"
                        )
                        return data["translatedFileUrl"]
                    elif response.status == 400:
                        self.logger.error(
                            f"Bad request during file translation: {data}"
                        )
                        raise Errors.BadRequest(str(data))
                    elif response.status == 403:
                        self.logger.error(f"Forbidden during file translation: {data}")
                        raise Errors.Forbidden(str(data))
                    elif response.status == 429:
                        self.logger.warning(
                            f"Rate limit during file translation: {data}"
                        )
                        raise Errors.RateLimitExceeded(str(data))
                    elif response.status == 500:
                        self.logger.error(
                            f"Server error during file translation: {data}"
                        )
                        raise Errors.InternalServerError(str(data))
                    else:
                        self.logger.error(f"Unexpected status code: {response.status}")
                        raise Errors.BadRequest(str(data))

    async def get_settings(self) -> dict:
        """
        Asynchronously retrieve settings from the translation API.

        Returns:
            dict: A dictionary containing the settings data.
        """
        self.logger.debug("Retrieving API settings")
        url = f"{self.url}/frontend/settings"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                settings = await response.json()
                self.logger.debug(f"Retrieved {len(settings)} settings")
                return settings

    async def validate_key(self) -> bool:
        """
        Asynchronously validate the API key.

        Returns:
            bool: True if the API key is valid, False otherwise.
        """
        self.logger.debug("Validating API key")
        result = (await self.detect("Hello"))["status"] == 200
        self.logger.info(f"API key validation: {'valid' if result else 'invalid'}")
        return result

    async def get_languages(self) -> list:
        """
        Asynchronously retrieve a list of supported languages from the translation API.

        Returns:
            list: A list of supported languages.
        """
        self.logger.debug("Retrieving supported languages")
        url = f"{self.url}/languages"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                languages = await response.json()
                self.logger.info(f"Retrieved {len(languages)} supported languages")
                return languages


if __name__ == "__main__":
    libretrans_api_key = ""
    libretrans_url = ""

    translator = API(api_key=libretrans_api_key, url=libretrans_url)
    print(asyncio.run(translator.translate_text("Hello, how are you?", "de")))
    print(asyncio.run(translator.translate_file("translation_test.txt", "de")))
