import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse

def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_website_links(url):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    # all URLs of `url`
    urls = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            # href empty tag
            continue
        # join the URL if it's relative (not an absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        # Normalize by removing trailing slash if it exists and the path is not empty
        if href.endswith('/') and parsed_href.path != '':
            href = href[:-1]
        if not is_valid(href):
            # not a valid URL
            continue
        if href in urls:
            # already in the set
            continue
        if domain_name not in href:
            # external link
            continue
        urls.add(href)
    return urls

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Link Extractor Tool")
    parser.add_argument("url", type=str, help="The URL to extract links from.")
    parser.add_argument("-o", "--output-file", type=str, default="urls.txt",
                        help="The output file to save the links to. Defaults to urls.txt")

    args = parser.parse_args()
    url = args.url
    output_file = f".outputs/{args.output_file}"

    links = get_all_website_links(url)

    # save the links to a file
    with open(output_file, "w") as f:
        for link in sorted(set(links)):  # Using set() to remove duplicates
            print(link, file=f)

    print(f"[+] Found {len(set(links))} unique links for {url}")
    print(f"[+] Links saved to {output_file}")