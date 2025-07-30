import requests
import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='.logs/fluentform_docs_extraction.log')

def extract_urls_from_sitemap_index(sitemap_index_url, output_file, filter_path=None):
    try:
        response = requests.get(sitemap_index_url)
        response.raise_for_status()
        logging.info(f"Successfully fetched sitemap index from {sitemap_index_url}")

        root = ET.fromstring(response.content)
        urls = []
        # Namespace for sitemap index
        ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        for sitemap_element in root.findall('sitemap:sitemap', ns):
            sitemap_loc = sitemap_element.find('sitemap:loc', ns)
            if sitemap_loc is not None and sitemap_loc.text:
                sub_sitemap_url = sitemap_loc.text
                logging.info(f"Parsing sub-sitemap: {sub_sitemap_url}")
                try:
                    sub_response = requests.get(sub_sitemap_url)
                    sub_response.raise_for_status()
                    sub_root = ET.fromstring(sub_response.content)
                    
                    # Namespace for sitemap URLs
                    url_ns = {'url': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

                    for url_element in sub_root.findall('url:url', url_ns):
                        loc = url_element.find('url:loc', url_ns)
                        if loc is not None and loc.text:
                            if filter_path and filter_path in loc.text:
                                urls.append(loc.text)
                            elif not filter_path:
                                urls.append(loc.text)
                except requests.exceptions.RequestException as e:
                    logging.error(f"Error fetching sub-sitemap {sub_sitemap_url}: {e}")
                except ET.ParseError as e:
                    logging.error(f"Error parsing sub-sitemap XML from {sub_sitemap_url}: {e}")

        with open(output_file, 'w') as f:
            for url in urls:
                f.write(url + '\n')
        logging.info(f"Successfully extracted {len(urls)} URLs and saved to {output_file}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching sitemap index from {sitemap_index_url}: {e}")
    except ET.ParseError as e:
        logging.error(f"Error parsing sitemap index XML from {sitemap_index_url}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    sitemap_index_url = "https://fluentforms.com/sitemap_index.xml"
    output_file = ".outputs/extracted_fluentform_docs_urls.txt"
    filter_path = "/docs/"
    extract_urls_from_sitemap_index(sitemap_index_url, output_file, filter_path)