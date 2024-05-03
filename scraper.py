import re
import hashlib
from collections import Counter
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Ignored extensions to filter out non-textual content
IGNORED_EXTENSIONS = set([
    '.css', '.js', '.bmp', '.gif', '.jpe', '.jpeg', '.jpg', '.ico', '.png', '.tif', '.tiff', '.pdf',
    '.mp3', '.mp4', '.avi', '.mov', '.mpeg', '.tar', '.gz', '.zip', '.rar', '.swf', '.flv', '.wma',
    '.wmv', '.ppsx', '.xlsx', '.ppt', '.pptx', 'xls', '.docx', '.exe', '.doc'
])

# Common stop words to ignore in text processing
STOP_WORDS = set("""
    a about above after again against all am an and any are aren't as at be because been before being below
    between both but by can't cannot could couldn't did didn't do does doesn't doing don't down during each few for
    from further had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him
    himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't
    my myself no nor not of off on once only or other ought our ours ourselves out over own same shan't she she'd
    she'll she's should shouldn't so some such than that that's the their theirs them themselves then there there's
    these they they'd they'll they're they've this those through to too under until up very was wasn't we we'd we'll
    we're we've were weren't what what's when when's where where's which while who who's whom why why's with won't
    would wouldn't you you'd you'll you're you've your yours yourself yourselves
""".split())

# Set of visited URLs to avoid revisiting the same page
visited_urls = set()
# Tracking the longest page by word count
longest_page = ('', 0)
# Counter for common words found across pages
common_words_counter = Counter()
# Dictionary to track subdomains and their pages
subdomain_pages = {}
# Pattern visits to detect URL patterns (trap detection)
pattern_visits = {}
# Set of content hashes to identify duplicate content
content_hashes = set()

def scraper(url, response):
    """Main scraping function to process each URL and its response."""
    if url in visited_urls:
        return []

    if url_meets_exclusion_criteria(url, response):
        print(f"Skipping URL {url} due to low content quality or trap.")
        return []

    final_url = handle_redirects(response)
    visited_urls.add(final_url)

    if is_content_duplicate(final_url, response.raw_response.content):
        return []

    word_count = count_words(response.raw_response.content)
    update_longest_page(final_url, word_count)
    register_subdomain(final_url)
    update_common_words(response.raw_response.content)

    return [link for link in extract_next_links(final_url, response) if is_valid(link)]

def url_meets_exclusion_criteria(url, response):
    """Check if URL meets any of the exclusion criteria."""
    return detect_trap(url) or is_dead_url(response) or not has_high_information_content(response)

def extract_next_links(url, response):
    """Extract and return all valid next links from the current URL response."""
    if response.status != 200 or not response.raw_response:
        return []

    soup = BeautifulSoup(response.raw_response.content, 'html.parser')
    return [make_absolute(url, link['href']) for link in
            soup.find_all('a', href=True) if is_valid(link['href'])]

def is_valid(link):
    """Check if a link is valid based on scheme, domain, and ignored extensions."""
    parsed = urlparse(link)
    return parsed.scheme in {"http", "https"} and re.match(
        r".*\.(ics|cs|informatics|stat)\.uci\.edu.*", parsed.netloc) and not any(
        parsed.path.lower().endswith(ext) for ext in IGNORED_EXTENSIONS)

def count_words(html_content):
    """Count words in HTML content, excluding HTML tags and scripts."""
    soup = BeautifulSoup(html_content, 'html.parser')
    words = re.findall(r'\b\w+\b', soup.get_text().lower())
    return len(words)

def update_longest_page(url, word_count):
    """Update record of the longest page by word count."""
    global longest_page
    if word_count > longest_page[1]:
        longest_page = (url, word_count)

def register_subdomain(url):
    """Register a subdomain and add the URL to its set."""
    subdomain = urlparse(url).netloc
    subdomain_pages.setdefault(subdomain, set()).add(url)

def update_common_words(html_content):
    """Update the count of common words found in the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    words = [word for word in re.findall(r'\b\w+\b', soup.get_text().lower()) if
             word not in STOP_WORDS]
    common_words_counter.update(words)

def handle_redirects(response):
    """Handle HTTP redirects."""
    if 300 <= response.status < 400:
        return urljoin(response.url, response.headers.get('Location', ''))
    return response.url

def detect_trap(url):
    """Detect if a URL is part of a trap based on repeated patterns."""
    pattern = re.sub(r'\d+', '[digit]', urlparse(url).path)
    pattern_visits[pattern] = pattern_visits.get(pattern, 0) + 1
    return pattern_visits[pattern] > 10

def is_dead_url(response):
    """Check if a URL is dead (status 200 but no content)."""
    return response.status == 200 and (
                not response.raw_response or len(response.raw_response.content) == 0)

def has_high_information_content(response):
    """Determine if a page has high informational content."""
    return response.raw_response and len(re.findall(r'\b\w+\b',
                                                    BeautifulSoup(response.raw_response.content,
                                                                  'html.parser').get_text().lower())) >= 100

def is_content_duplicate(url, html_content):
    """Check if the content of a URL is a duplicate of previously seen content."""
    content_hash = hashlib.md5(
        BeautifulSoup(html_content, 'html.parser').get_text().encode('utf-8')).hexdigest()
    if content_hash in content_hashes:
        print(f"Duplicate content detected at {url}.")
        return True
    content_hashes.add(content_hash)
    return False

def make_absolute(base_url, link):
    """Convert a relative URL link to an absolute URL based on the base URL."""
    return urljoin(base_url, link)
