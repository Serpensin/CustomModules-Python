import asyncio

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

    def __init__(self, APIkey, url):
        """
        Initialize the API object.

        Args:
            APIkey (str): The API key for accessing the translation API.
            url (str): The base URL of the translation API.

        Raises:
            Errors.InvalidAPIKey: If the provided API key is invalid.
        """
        self.APIkey = APIkey
        self.url = url.rstrip("/")
        if not asyncio.run(self.validate_key()):
            raise Errors.InvalidAPIKey()

    def _get_sample(self, text, isFile=False) -> str:
        """
        Extract a sample text from either a string or a file.

        Args:
            text (str): The input text or path to the file.
            isFile (bool): Indicates whether the input is a file path.

        Returns:
            str: The sample text.
        """
        if isFile:
            with open(text, "r") as file:
                text = file.read()

        first_words = text.split(" ")
        return " ".join(first_words[:20])

    async def detect(self, text) -> dict:
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
        url = f"{self.url}/detect"
        params = {"q": text, "api_key": self.APIkey}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, params=params) as response:
                    data = await response.json()
                    response_data = {"status": response.status, "data": data}
                    if response.status == 200:
                        return response_data
                    elif response.status == 400:
                        raise Errors.BadRequest(response_data)
                    elif response.status == 403:
                        raise Errors.Forbidden(response_data)
                    elif response.status == 429:
                        raise Errors.RateLimitExceeded(response_data)
                    elif response.status == 500:
                        raise Errors.InternalServerError(response_data)
            except aiohttp.ClientConnectorDNSError:
                raise Errors.InvalidAPIKey(
                    "Invalid URL or unable to connect to the server."
                )

    async def translate_text(self, text, dest_lang, source="") -> str:
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
        url = f"{self.url}/translate"
        if not source:
            source = (await self.detect(self._get_sample(text)))["data"][0]["language"]
        params = {
            "q": text,
            "source": source,
            "target": dest_lang,
            "api_key": self.APIkey,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                data = await response.json()
                if response.status == 200:
                    return data["translatedText"]
                elif response.status == 400:
                    raise Errors.BadRequest(data)
                elif response.status == 403:
                    raise Errors.Forbidden(data)
                elif response.status == 429:
                    raise Errors.RateLimitExceeded(data)
                elif response.status == 500:
                    raise Errors.InternalServerError(data)

    async def translate_file(self, file, dest_lang, source="") -> str:
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
        url = f"{self.url}/translate_file"
        if not source:
            source = (await self.detect(self._get_sample(file, True)))["data"][0][
                "language"
            ]
        form = aiohttp.FormData()
        form.add_field("source", source)
        form.add_field("target", dest_lang)
        form.add_field("api_key", self.APIkey)
        with open(file, "rb") as f:
            form.add_field(
                "file", f, filename=file, content_type="application/octet-stream"
            )
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form) as response:
                    data = await response.json()
                    if response.status == 200:
                        return data["translatedFileUrl"]
                    elif response.status == 400:
                        raise Errors.BadRequest(data)
                    elif response.status == 403:
                        raise Errors.Forbidden(data)
                    elif response.status == 429:
                        raise Errors.RateLimitExceeded(data)
                    elif response.status == 500:
                        raise Errors.InternalServerError(data)

    async def get_settings(self) -> dict:
        """
        Asynchronously retrieve settings from the translation API.

        Returns:
            dict: A dictionary containing the settings data.
        """
        url = f"{self.url}/frontend/settings"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    async def validate_key(self) -> bool:
        """
        Asynchronously validate the API key.

        Returns:
            bool: True if the API key is valid, False otherwise.
        """
        return (await self.detect("Hello"))["status"] == 200

    async def get_languages(self) -> list:
        """
        Asynchronously retrieve a list of supported languages from the translation API.

        Returns:
            list: A list of supported languages.
        """
        url = f"{self.url}/languages"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()


if __name__ == "__main__":
    libretransAPIkey = ""
    libretransURL = ""

    translator = API(APIkey=libretransAPIkey, url=libretransURL)
    print(asyncio.run(translator.translate_text("Hello, how are you?", "de")))
    print(asyncio.run(translator.translate_file("translation_test.txt", "de")))
