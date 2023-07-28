from googlesearch import search
import bs4
from selenium import webdriver


def get_query(query):
    # get first 2 .edu and .org results from google
    links_to_scrape = []
    for link in search(query + " site:wikipedia.org", num_results=1):
        links_to_scrape.append(link)
    for link in search(query, num_results=2):
        links_to_scrape.append(link)
    # for link in search(query + " site:edu", num_results=2):
    #     links_to_scrape.append(link)

    # instantiate chrome driver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # somewhat broken
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)

    page_text = []
    for link in links_to_scrape:
        try:
            driver.get(link)
            soup = bs4.BeautifulSoup(driver.page_source, "html.parser")
            blocklist = [
                "style",
                "script",
                # other elements,
            ]
            text_content = [
                t.text.replace("\n", " ").replace("\t", " ").replace("\r", " ").replace("  ", "")
                for t in soup.find_all(text=True)
                if t.parent.name not in blocklist
            ]
            page_text.append(" ".join(text_content))
        except:
            pass
    driver.close()
    with open("page_text.txt", "w") as f: # DEBUG
        f.write(" ".join(page_text))
    return " ".join(page_text)

