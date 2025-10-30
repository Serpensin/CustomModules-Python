import logging
import re
from typing import Optional

import aiohttp
import html2text
from bs4 import BeautifulSoup

# Module logger
_logger: Optional[logging.Logger] = None


def set_logger(logger: Optional[logging.Logger] = None) -> None:
    """
    Set the logger for this module.

    Args:
        logger (Optional[logging.Logger]): Parent logger. If provided, creates a child logger
        under CustomModules.Patchnotes. Defaults to None.
    """
    global _logger
    if logger:
        _logger = logger.getChild("CustomModules").getChild("Patchnotes")
    else:
        _logger = logging.getLogger("CustomModules.Patchnotes")
    _logger.debug("Patchnotes logger configured")


async def get_update_content(
    version: str, return_type: str = "html"
) -> Optional[str]:
    """
    Gets the content of the given update from a 3rd party website.

    Parameters
    ----------
    version : str
        The version of the update to get the content of.
    return_type : str, optional
        The format to return the data in. Can be either 'html' or 'md'. Defaults to 'html'.

    Returns
    -------
    Optional[str]
        The content of the update in the requested format, or None if not found.

    Raises
    ------
    ValueError
        If the return type is not 'html' or 'md'.
        If the given version is invalid.

    Notes
    -----
    The content is retrieved from https://dbd.tricky.lol/patchnotes.
    """
    if _logger:
        _logger.debug(
            f"Getting update content for version {version}, return type: {return_type}"
        )

    if return_type not in ["html", "md"]:
        if _logger:
            _logger.error(f"Invalid return type: {return_type}")
        raise ValueError(
            "Invalid return type. Return type needs to be either 'html' or 'md'."
        )

    url = "https://dbd.tricky.lol/patchnotes"
    converter = html2text.HTML2Text()
    converter.ignore_links = True

    version = __validate_and_format(version)
    if _logger:
        _logger.debug(f"Formatted version: {version}")

    async with aiohttp.ClientSession() as session:
        if _logger:
            _logger.debug(f"Fetching patchnotes from {url}")
        async with session.get(url) as response:
            page_content = await response.text()
            soup = BeautifulSoup(page_content, "html.parser")
            update_divs = soup.find_all("div", class_="update")

            if _logger:
                _logger.debug(f"Found {len(update_divs)} update divs")

            for update_div in update_divs:
                h1_tags = update_div.find_all("h1")
                for h1 in h1_tags:
                    if version in h1.text:
                        if _logger:
                            _logger.info(
                                f"Found matching patchnotes for version {version}"
                            )
                        if return_type == "html":
                            return update_div.prettify()
                        elif return_type == "md":
                            return converter.handle(update_div.prettify())

    if _logger:
        _logger.warning(f"No patchnotes found for version {version}")
    return None


def __validate_and_format(version):
    if _logger:
        _logger.debug(f"Validating version format: {version}")

    if not re.fullmatch(r"([5-9]|[1-9]\d)\.\d\.\d", version) and not re.fullmatch(
        r"[5-9]\d{2}|[1-9]\d{3}", version
    ):
        if _logger:
            _logger.error(f"Invalid version format: {version}")
        raise ValueError(
            "Invalid version format. Version needs to be at least 5.0.0 or 500."
        )
    version = version.replace(".", "")
    version = list(version)
    version.insert(-1, ".")
    version.insert(-3, ".")
    formatted = "".join(version)

    if _logger:
        _logger.debug(f"Formatted version from {version} to {formatted}")

    return formatted


if __name__ == "__main__":
    import asyncio

    version = "6.7.1"
    content = asyncio.run(get_update_content(version, "md"))
    if content:
        print(content)
        with open("Markdown.md", "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print(f"No patchnotes found for version {version}")
