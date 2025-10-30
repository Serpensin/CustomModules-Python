import logging
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
        under CustomModules.Killswitch. Defaults to None.
    """
    global _logger
    if logger:
        _logger = logger.getChild("CustomModules").getChild("Killswitch")
    else:
        _logger = logging.getLogger("CustomModules.Killswitch")
    _logger.debug("Killswitch logger configured")


async def get_killswitch(return_type: str = "html") -> str | None:
    """
    Gets the current Kill Switch status from the official Dead by Daylight website.

    Parameters
    ----------
    return_type : str, optional
        The format to return the data in. Can be either 'html' or 'md'. Defaults to 'html'.

    Returns
    -------
    str
        The Kill Switch status in the requested format.

    Raises
    ------
    ValueError
        If the return type is not 'html' or 'md'.

    Notes
    -----
    The content is retrieved from https://forums.bhvr.com/dead-by-daylight/kb/articles/299-kill-switch-master-list.
    """
    if _logger:
        _logger.debug(f"Fetching killswitch status (return_type={return_type})")

    if return_type not in ["html", "md"]:
        if _logger:
            _logger.error(f"Invalid return type: {return_type}")
        raise ValueError(
            "Invalid return type. Return type needs to be either 'html' or 'md'."
        )

    url = "https://forums.bhvr.com/dead-by-daylight/kb/articles/299-kill-switch-master-list"
    converter = html2text.HTML2Text()
    converter.ignore_links = True

    if _logger:
        _logger.debug(f"Fetching data from {url}")

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if _logger:
                _logger.debug(f"Received response with status {response.status}")

            page_content = await response.text()
            soup = BeautifulSoup(page_content, "html.parser")

            # Find the required sections
            kill_switch_section = soup.find("h2", {"data-id": "kill-switch-disabled"})
            known_issues_section = soup.find(
                "h2", {"data-id": "known-issues-not-disabled"}
            )

            if not kill_switch_section or not known_issues_section:
                if _logger:
                    _logger.warning("Could not find required sections on the page")
                return None

            # Extract the content between the two sections
            content = []
            for sibling in kill_switch_section.find_next_siblings():
                if sibling == known_issues_section:
                    break
                # Remove any images
                for img in sibling.find_all("img"):
                    img.decompose()
                content.append(str(sibling))

            # Convert the content to the required format
            content = "\n".join(content)
            if not content:
                if _logger:
                    _logger.warning("No content found between sections")
                return None

            if return_type == "html":
                if _logger:
                    _logger.info(
                        f"Returning HTML killswitch status ({len(content)} chars)"
                    )
                return content

            md_content = converter.handle(content)
            if _logger:
                _logger.info(
                    f"Returning Markdown killswitch status ({len(md_content)} chars)"
                )
            return md_content

    return None


if __name__ == "__main__":
    import asyncio

    md = asyncio.run(get_killswitch("md"))
    print(md)
