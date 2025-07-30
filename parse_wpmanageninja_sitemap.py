import requests
import xml.etree.ElementTree as ET

def parse_sitemap(sitemap_url, output_file, url_filter=None):
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sitemap: {e}")
        return

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return

    # Namespaces can be tricky with XML parsing. Find the namespace.
    # A common sitemap namespace is 'http://www.sitemaps.org/schemas/sitemap/0.9'
    # We can extract it from the root tag if it's present.
    namespace = ''
    if '}' in root.tag:
        namespace = root.tag.split('}')[0][1:]

    urls = []
    sitemap_urls = []
    # Check if it's a sitemap index file
    for sitemap_element in root.findall(f'{{{namespace}}}sitemap'):
        loc_element = sitemap_element.find(f'{{{namespace}}}loc')
        if loc_element is not None:
            sitemap_urls.append(loc_element.text)

    if sitemap_urls: # It's a sitemap index, recursively parse each sitemap
        all_urls = []
        for sub_sitemap_url in sitemap_urls:
            print(f"Parsing sub-sitemap: {sub_sitemap_url}")
            all_urls.extend(parse_sitemap(sub_sitemap_url, None, url_filter)) # Pass None for output_file to collect URLs
        return all_urls
    else: # It's a regular sitemap
        urls = []
        for url_element in root.findall(f'{{{namespace}}}url'):
            loc_element = url_element.find(f'{{{namespace}}}loc')
            if loc_element is not None:
                urls.append(loc_element.text)
        if url_filter:
            urls = [url for url in urls if url_filter in url]
        return urls

    if output_file:
        with open(output_file, 'w') as f:
            for url in urls:
                f.write(url + '\n')
        print(f"Successfully extracted {len(urls)} URLs to {output_file}")
    return urls

if __name__ == "__main__":
    sitemap_url = "https://wpmanageninja.com/sitemap_index.xml"
    output_file = ".outputs/extracted_urls.txt" # This file will be created in the .outputs directory
    filter_path = "docs/fluent-form"
    
    all_extracted_urls = parse_sitemap(sitemap_url, None, filter_path) # Initially parse without writing to file

    if all_extracted_urls:
        # Write all collected URLs to the final output file
        with open(output_file, 'w') as f:
            for url in all_extracted_urls:
                f.write(url + '\n')
        print(f"Total URLs extracted and saved to {output_file}: {len(all_extracted_urls)}")
    else:
        print("No URLs extracted.")