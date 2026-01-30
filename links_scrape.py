from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


chrome_options = Options()
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

url = "https://www.fertilityfriday.com/episodes/"

def get_episode_links():
    print("get_episode_links() called")

    try:
        print("Opening page...")
        driver.get(url)
        time.sleep(3)

        print("Finding elements using selector...")
        elements = driver.find_elements(By.CSS_SELECTOR, ".entry-content p a")

        print(f"Elements found: {len(elements)}")

        links = []
        for idx, el in enumerate(elements):
            href = el.get_attribute("href")
            print(f"   [{idx}] href = {href}")
            if href:
                links.append(href)

        print(f"Total valid links collected: {len(links)}")
        return links

    except Exception as e:
        print("ERROR inside get_episode_links():", e)
        return []

    finally:
        print("Closing browser")
        driver.quit()

