import aiohttp




class LibreTranslateAPI:
    """
    A wrapper for the LibreTranslate API.

    Parameters
    ----------
    APIkey : str
        The API key to use for the API.
    url : str
        The URL of the API.
    """
    def __init__(self, APIkey, url):
        self.APIkey = APIkey
        self.url = url


    async def _get_sample(self, text):
        sentences = text.split('. ')
        first_sentence_words = sentences[0].split(' ')

        if len(first_sentence_words) > 10:
            sample = ' '.join(first_sentence_words[:10])
        else:
            sample = ' '.join(first_sentence_words)

        return sample


    async def detect(self, text):
        """
        Detects the language of the given text.

        Parameters
        ----------
        text : str
            The text to detect the language of.

        Returns
        -------
        dict
            A dictionary containing the status code and the data.
        200: The request was successful.
        400: The request was invalid.
        500: The server encountered an error.
        """
        url = f"{self.url}/detect"
        params = {
            "q": text,
            "api_key": self.APIkey
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                data = await response.json()
                return {"status": response.status, "data": data}


    async def translate(self, text, dest_lang, source = ''):
        """
        Translates the given text to the given language.

        Parameters
        ----------
        text : str
            The text to translate.
        dest_lang : str
            The language to translate the text to.
        source : str, optional
            The language of the text. If not given, it will be detected automatically.

        Returns
        -------
        dict
            A dictionary containing the status code and the data.
        200: The request was successful.
        400: The request was invalid.
        500: The server encountered an error.
        """
        url = f'{self.url}/translate'
        if source == '':
            source = await self.detect(await self._get_sample(text))
            source = source["data"][0]["language"]
        params = {
            "q": text,
            "source": source,
            "target": dest_lang,
            "api_key": self.APIkey
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    data = await response.json()
                    return {"status": response.status, "data": data}
        except:
            return {"status": 500, "data": None}


    async def check_status(self):
        """
        Checks the status of the API.

        Returns
        -------
        bool
            Whether the API is online or not.
        """
        url = f'{self.url}/frontend/settings'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return response.status == 200
        except:
            return False



if __name__ == '__main__':
    print('This is a module for the LibreTranslate API wrapper.')