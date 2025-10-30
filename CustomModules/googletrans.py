import logging
from typing import Optional

from google.auth.exceptions import RefreshError
from google.cloud import translate_v2


class API:
    """
    A class for interacting with the Google Cloud Translate API.

    Attributes:
        credentials_path (str): The path to the JSON file containing Google Cloud service account credentials.
        translate_client: The client for interacting with the Google Cloud Translate API.
        logger: Logger instance for this class.
    """

    def __init__(self, credentials_path: str, logger: Optional[logging.Logger] = None):
        """
        Initializes the API instance.

        Args:
            credentials_path (str): The path to the JSON file containing Google Cloud service account credentials.
            logger (Optional[logging.Logger]): Parent logger. If provided, creates a child logger
            under CustomModules.Googletrans. Defaults to None.

        Raises:
            Exception: If failed to verify credentials.
        """
        # Setup logger with child hierarchy: parent -> CustomModules -> Googletrans
        if logger:
            self.logger = logger.getChild("CustomModules").getChild("Googletrans")
        else:
            self.logger = logging.getLogger("CustomModules.Googletrans")

        self.logger.debug(
            f"Initializing Google Translate API with credentials from {credentials_path}"
        )

        self.credentials_path = credentials_path
        try:
            self.translate_client = translate_v2.Client.from_service_account_json(
                self.credentials_path
            )
            self.logger.debug("Successfully created translate client")
        except Exception as e:
            self.logger.error(f"Failed to create translate client: {e}")
            raise

        if not self.check_credentials():
            self.logger.error("Credential verification failed")
            raise ValueError("Failed to verify credentials.")

        self.logger.info("Google Translate API initialized successfully")

    def _get_sample(self, text) -> str:
        """
        Returns the first 20 words or less of the input text.

        Args:
            text (str): The input text.

        Returns:
            str: The first 20 words or less of the input text.
        """
        return " ".join(text.split()[:20])

    def translate_text(
        self, text: str, target_language: str, source_language: str = ""
    ) -> str:
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
        self.logger.debug(
            f"Translating text to {target_language} (source: {source_language or 'auto'})"
        )
        try:
            result = self.translate_client.translate(
                text, target_language=target_language, source_language=source_language
            )
            translated = result["translatedText"]
            self.logger.debug(
                f"Translation successful: '{self._get_sample(text)}' -> '{self._get_sample(translated)}'"
            )
            return translated
        except (FileNotFoundError, RefreshError) as e:
            self.logger.error(f"Translation failed: {e}")
            raise

    def check_credentials(self) -> bool:
        """
        Verifies that the provided credentials are valid.

        Returns:
            bool: True if credentials are valid, False otherwise.

        Raises:
            FileNotFoundError: If credentials file is not found.
            RefreshError: If there is an error refreshing credentials.
        """
        self.logger.debug("Verifying credentials")
        try:
            result = self.translate_client.translate("Ping", target_language="en")
            is_valid = result.get("translatedText") == "Ping"
            self.logger.info(
                f"Credential verification: {'successful' if is_valid else 'failed'}"
            )
            return is_valid
        except (FileNotFoundError, RefreshError) as e:
            self.logger.error(f"Credential verification failed: {e}")
            raise

    def get_languages(self) -> dict:
        """
        Retrieves a dictionary of supported languages.

        Returns:
            dict: A dictionary containing supported languages.

        Raises:
            FileNotFoundError: If credentials file is not found.
            RefreshError: If there is an error refreshing credentials.
        """
        self.logger.debug("Retrieving supported languages")
        try:
            languages = self.translate_client.get_languages()
            self.logger.debug(f"Retrieved {len(languages)} supported languages")
            return languages
        except (FileNotFoundError, RefreshError) as e:
            self.logger.error(f"Failed to retrieve languages: {e}")
            raise

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
        self.logger.debug(f"Detecting language for: '{self._get_sample(text)}'")
        try:
            result = self.translate_client.detect_language(text)
            detected_lang = result["language"]
            self.logger.debug(f"Detected language: {detected_lang}")
            return detected_lang
        except (FileNotFoundError, RefreshError) as e:
            self.logger.error(f"Language detection failed: {e}")
            raise


if __name__ == "__main__":
    credentials_path = "googleauth.json"
    translator = API(credentials_path)

    text = "Hello World."
    translated_text = translator.translate_text(text, target_language="de")
    print(translated_text)
