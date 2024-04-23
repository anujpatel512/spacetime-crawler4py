import re
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin, urldefrag
import utils


def scraper (url: str, resp: utils.response.Response):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]



def extract_next_links(url, resp):
    # List to hold the extracted URLs
    extracted_urls = []

    # Use Python's built-in HTMLParser to parse the content
    parser = HTMLParser()

    # Function to handle starttag event
    def handle_starttag(tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    # Make the URL absolute by joining it with the base URL
                    abs_url = urljoin(url, attr[1])
                    # Defragment the URL
                    defragmented_url, _ = urldefrag(abs_url)
                    extracted_urls.append(defragmented_url)

    # Assign the handle_starttag function to the parser's starttag event handler
    parser.handle_starttag = handle_starttag

    # Decode the response content and feed it to the parser
    html_content = resp.raw_response.content.decode('utf-8', errors='ignore')
    parser.feed(html_content)

    return extracted_urls
def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        valid_domains = [
            ".ics.uci.edu",
            ".cs.uci.edu",
            ".informatics.uci.edu",
            ".stat.uci.edu"
        ]
        if not any(domain in parsed.netloc for domain in valid_domains):
            return False

        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False

        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
