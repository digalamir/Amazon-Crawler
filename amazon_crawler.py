from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os

def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox") # Bypass OS security (required for ubuntu)
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems (required for ubuntu)
    options.add_argument("--disable-gpu") # Disable GPU acceleration (required for headless mode on Ubuntu)
    options.add_argument("--window-size=1920,1080") # Set window size to avoid issues with elements not being found
    options.add_argument("--lang=en-US") # Set language to English
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 "
    )
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    
    return driver

# Function to scrape product details from the current page
def scrape_page(driver):
    products = []
    
    # wait until products cards are loaded
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, '//div[@data-component-type="s-search-result"]')
        )
    )
    
    items = driver.find_elements(
        By.XPATH, '//div[@data-component-type="s-search-result"]'
    )
    
    for item in items:
        try:
            # Product Title
            title = item.find_element(
                By.XPATH, './/h2/span'
            ).text.strip()
        except:
            title = "N/A"
    
        # try:
        #     # Product Price
        #     price = item.find_element(
        #         By.XPATH, './/span[@class="a-price-whole"]'
        #     ).text.strip()
        #     price = f"£{price}"
        # except:
        #     price = "N/A"

        # try:
        #     # Star Rating
        #     rating = item.find_element(
        #         By.XPATH, './/span[@class="a-icon-alt"]'
        #     ).get_attribute("innerHTML").strip()
        # except:
        #     rating = "N/A"

        # try:
        #     # Number of Reviews
        #     reviews = item.find_element(
        #         By.XPATH, './/span[@data-component-type="s-client-side-analytics"]//span[@aria-label]'
        #     ).get_attribute("aria-label").strip()
        # except:
        #     reviews = "N/A"

        # try:
        #     # Product URL
        #     url = item.find_element(
        #         By.XPATH, './/h2/a'
        #     ).get_attribute("href")
        # except:
        #     url = "N/A"

        products.append({
            "Title": title,
            # "Price": price,
            # "Rating": rating,
            # "Reviews": reviews,
            # "URL": url
        })
        
    return products

# Paginated and Collection of upto 100 Results
def crawl_amazon(keyword, max_results = 100):
    driver = setup_driver()
    all_products = []
    page = 1
    
    print(f"\n Searching Amazon for '{keyword}' ")
    
    while len(all_products) < max_results:
        url = f"https://www.amazon.co.uk/s?k={keyword.replace(' ', '+')}&page={page}"
        print(f"Scraping page {page}... URL: {url}")
        
        driver.get(url)
        time.sleep(3)  # Wait for the page to load
        
        try:
            page_products = scrape_page(driver)
            print(f"Products on this page: {len(page_products)}")
        
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            break
        
        if not page_products:
            print("No more products found, stopping.")
            break
        
        all_products.extend(page_products)
        print(f"Collected {len(all_products)} products so far...")
        
        # Check if next page button is available
        try:
            next_button = driver.find_element(
                By.XPATH, '//a[contains(@class, "s-pagination-next")]'
            )
            if "s-pagination-disabled" in next_button.get_attribute("class"):
                print("Next page button is disabled (Reached last page), stopping.")
                break
            page += 1
            
        except:
            print("No more pages available.")
            break
        
    driver.quit()
    
    # Trim the results to max_results
    return all_products[:max_results]

        
# Save Results to CSV
def save_results(products, keyword):
    os.makedirs("results", exist_ok = True)
    # cleaning keyword to avoid bad characters in filename
    clean_keyword = "".join(c if c.isalnum() or c == " " else "_" for c in keyword)
    filename = f"results/{clean_keyword.replace(' ', '_')}_product_results.xlsx"
    
    df = pd.DataFrame(products)
    df.to_excel(filename, index = False, engine = "openpyxl")
    
    print(f"\nResults saved to: {filename}")
    print(df.head())
    
    
# Main Entry Point
if __name__ == "__main__":
    keyword = input("Enter search keyword: ")
    results = crawl_amazon(keyword, max_results = 100)
    
    if results:
        save_results(results, keyword)
        print(f"\n Total Products scraped: {len(results)}")
        
    else:
        print("No Products Found.")