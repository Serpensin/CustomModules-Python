import aiohttp



class LibreTranslateAPI:
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
        url = f"{self.url}/detect"
        params = {
            "q": text,
            "api_key": self.APIkey
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    data = await response.json()
                    return {"status": response.status, "data": data}
        except:
            raise Exception("An error occurred while trying to connect to the LibreTranslate API.")

    async def translate(self, text, dest_lang, source = '') -> str:
        url = f'{self.url}/translate'
        if source == '':
            try:
                source = await self.detect(await self._get_sample(text))
                source = source["data"][0]["language"]
            except:
                raise Exception("An error occurred while trying to detect the language of the text.")
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
                    return data['translatedText']
        except:
            raise Exception("An error occurred while trying to connect to the LibreTranslate API.")

    async def get_settings(self):
        url = f'{self.url}/frontend/settings'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
        except:
            return None

    async def validate_key(self) -> bool:
        data = await self.detect("Hello")
        return data["status"] == 200






if __name__ == '__main__':
    print('This is a module for the LibreTranslate API wrapper.')