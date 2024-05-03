import re
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin, urldefrag
import utils


def scraper (url: str, resp: utils.response.Response):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def defragment_url(url):
    return url.split('#')[0]

def extract_next_links(url, resp):
    soup = BeautifulSoup(html_content, 'html.parser')
    scraped_urls = []

    # Extract all links
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            # Clean and validate the URL
            clean_url = defragment_url(href)
            if is_valid(clean_url):
                scraped_urls.append(clean_url)

    return scraped_urls

def is_valid(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme in ('http', 'https') and \
        'ics.uci.edu' in parsed_url.netloc
