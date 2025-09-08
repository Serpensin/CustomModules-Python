import aiohttp
import html2text
from bs4 import BeautifulSoup

async def get_killswitch(return_type: str = 'html') -> str | None:
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
    if return_type not in ['html', 'md']:
        raise ValueError("Invalid return type. Return type needs to be either 'html' or 'md'.")

    url = 'https://forums.bhvr.com/dead-by-daylight/kb/articles/299-kill-switch-master-list'
    converter = html2text.HTML2Text()
    converter.ignore_links = True

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            page_content = await response.text()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Find the required sections
            kill_switch_section = soup.find('h2', {'data-id': 'kill-switch-disabled'})
            known_issues_section = soup.find('h2', {'data-id': 'known-issues-not-disabled'})

            if not kill_switch_section or not known_issues_section:
                return None

            # Extract the content between the two sections
            content = []
            for sibling in kill_switch_section.find_next_siblings():
                if sibling == known_issues_section:
                    break
                # Remove any images
                for img in sibling.find_all('img'):
                    img.decompose()
                content.append(str(sibling))

            # Convert the content to the required format
            content = '\n'.join(content)
            if not content:
                return None
            if return_type == 'html':
                return content
            return converter.handle(content)

    return None

if __name__ == '__main__':
    import asyncio
    md = asyncio.run(get_killswitch('md'))
    print(md)
