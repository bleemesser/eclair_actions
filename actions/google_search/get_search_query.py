from googlesearch import search
import os, json, requests
import bs4
from selenium import webdriver
import time

def scrape_content(links_to_scrape):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # somewhat broken
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)

    page_text = []
    for link in links_to_scrape:
        try:
            # print(f"Fetching content from {link}")
            driver.get(link)
            soup = bs4.BeautifulSoup(driver.page_source, "html.parser")
            blocklist = [
                "style",
                "script",
                # other elements,
            ]
            text_content = [
                t.text.replace("\n", " ")
                .replace("\t", " ")
                .replace("\r", " ")
                .replace("  ", "")
                for t in soup.find_all(string=True)
                if t.parent.name not in blocklist
            ]
            page_text.append(" ".join(text_content))
        except:
            pass
            # print(f"Failed to fetch content from {link}")
    driver.close()
    # with open("page_text.txt", "w") as f: # DEBUG
    #     f.write(" ".join(page_text))
    return " ".join(page_text)

def get_google_query(query):
    # get first 2 .edu and .org results from google
    links_to_scrape = []
    try:
        for link in search(
            query + " site:wikipedia.org", num_results=1, sleep_interval=5
        ):
            links_to_scrape.append(link)
        links_to_scrape = [links_to_scrape[0]]
    except:
        time.sleep(300)
        for link in search(
            query + " site:wikipedia.org", num_results=1, sleep_interval=5
        ):
            links_to_scrape.append(link)
        links_to_scrape = [links_to_scrape[0]]
    # print(links_to_scrape)
    try:
        for link in search(query, num_results=1, sleep_interval=5):
            links_to_scrape.append(link)
        links_to_scrape = [links_to_scrape[0], links_to_scrape[1]]
    except:
        time.sleep(300)
        for link in search(query, num_results=1, sleep_interval=5):
            links_to_scrape.append(link)
        links_to_scrape = [links_to_scrape[0], links_to_scrape[1]]
    # for link in search(query + " site:edu", num_results=2):
    #     links_to_scrape.append(link)
    # print(links_to_scrape)
    return scrape_content(links_to_scrape)

def get_bing_query(query):
    key = os.environ["BING_KEY"]
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    
    mkt = "en-US"
    params = {"q": query, "mkt": mkt}
    headers = {"Ocp-Apim-Subscription-Key": key}
    
    try: 
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        # print(search_results["webPages"]["value"])
        if len(search_results["webPages"]["value"]) < 2:
            raise Exception("Not enough results")
        links = [search_results["webPages"]["value"][i]["url"] for i in range(2)]
        # print(links)
    except Exception as ex:
        raise ex
    return scrape_content(links)

