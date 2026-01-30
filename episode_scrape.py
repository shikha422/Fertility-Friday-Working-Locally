from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from scrape import get_episode_links
import multiprocessing as mp
import json

BATCH_SIZE = 100
NUM_WORKERS = 6   # 4 parallel browsers

def scrape_batch(worker_id, links, start_index):
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    wait = WebDriverWait(driver, 10)
    results = []

    try:
        for idx, url in enumerate(links, start=start_index):
            print(f"[Worker {worker_id}] [{idx}] Scraping {url}")
            driver.get(url)

            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".entry-content"))
            )

            try:
                title = driver.find_element(By.CSS_SELECTOR, "h1.entry-title").text
            except:
                title = "Title not found"

            try:
                content = driver.find_element(By.CSS_SELECTOR, ".entry-content").text
            except:
                content = "Content not found"

            results.append({
                "url": url,
                "title": title,
                "main_text": content
            })

    finally:
        driver.quit()

    with open(f"new{worker_id}.", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Worker {worker_id} finished")

if __name__ == "__main__":
    episode_links = get_episode_links()
    total = len(episode_links)

    print(f"🔎 Total episodes: {total}")

    processes = []

    for worker_id in range(NUM_WORKERS):
        start = worker_id * BATCH_SIZE
        end = start + BATCH_SIZE
        batch = episode_links[start:end]

        if not batch:
            break

        p = mp.Process(
            target=scrape_batch,
            args=(worker_id, batch, start + 1)
        )
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print("🚀 Parallel batch complete")