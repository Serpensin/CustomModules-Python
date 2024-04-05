from google.auth.exceptions import RefreshError
from google.cloud import translate_v2



class API:
    """
    A class for interacting with the Google Cloud Translate API.

    Attributes:
        credentials_path (str): The path to the JSON file containing Google Cloud service account credentials.
        translate_client: The client for interacting with the Google Cloud Translate API.
    """

    def __init__(self, credentials_path: str):
        """
        Initializes the API instance.

        Args:
            credentials_path (str): The path to the JSON file containing Google Cloud service account credentials.

        Raises:
            Exception: If failed to verify credentials.
        """
        self.credentials_path = credentials_path
        self.translate_client = translate_v2.Client.from_service_account_json(self.credentials_path)

        if not self.check_credentials():
            raise Exception("Failed to verify credentials.")

    def _get_sample(self, text) -> str:
        """
        Returns the first 20 words or less of the input text.

        Args:
            text (str): The input text.

        Returns:
            str: The first 20 words or less of the input text.
        """
        first_words = text.split(' ')
        if len(first_words) > 20:
            sample = ' '.join(first_words[:20])
        else:
            sample = ' '.join(first_words)

        return sample

    def translate_text(self, text: str, target_language: str, source_language: str = "") -> str:
        """
        Translates text from a source language to a target language.

        Args:
            text (str): The text to translate.
            target_language (str): The language to translate the text into.
            source_language (str, optional): The language of the input text. Defaults to "".

        Returns:
            str: The translated text.

        Raises:
            FileNotFoundError: If credentials file is not found.
            RefreshError: If there is an error refreshing credentials.
        """
        try:
            result = self.translate_client.translate(text, target_language=target_language, source_language=source_language)
            return result["translatedText"]
        except (FileNotFoundError, RefreshError) as e:
            raise e

    def check_credentials(self) -> bool:
        """
        Verifies that the provided credentials are valid.

        Returns:
            bool: True if credentials are valid, False otherwise.

        Raises:
            FileNotFoundError: If credentials file is not found.
            RefreshError: If there is an error refreshing credentials.
        """
        try:
            result = self.translate_client.translate("Ping", target_language="en")
            return result.get("translatedText") == "Ping"
        except (FileNotFoundError, RefreshError) as e:
            raise e

    def get_languages(self) -> dict:
        """
        Retrieves a dictionary of supported languages.

        Returns:
            dict: A dictionary containing supported languages.

        Raises:
            FileNotFoundError: If credentials file is not found.
            RefreshError: If there is an error refreshing credentials.
        """
        try:
            languages = self.translate_client.get_languages()
            return languages
        except (FileNotFoundError, RefreshError) as e:
            raise e

    def detect_language(self, text: str) -> str:
        """
        Detects the language of the input text.

        Args:
            text (str): The input text.

        Returns:
            str: The detected language.

        Raises:
            FileNotFoundError: If credentials file is not found.
            RefreshError: If there is an error refreshing credentials.
        """
        try:
            result = self.translate_client.detect_language(text)
            return result["language"]
        except (FileNotFoundError, RefreshError) as e:
            raise e







if __name__ == '__main__':
    credentials_path = "googleauth.json"
    translator = API(credentials_path)

    text = "Hello World."
    translated_text = translator.translate_text(text, target_language="de")
    print(translated_text)
