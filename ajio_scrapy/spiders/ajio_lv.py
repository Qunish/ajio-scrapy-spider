import scrapy
from selenium.webdriver.common.by import By
import pymongo
from ..items import AjioScrapyItem_LV
import random
import time

DRIVER_FILE_PATH = "/Users/qunishdash/Documents/chromedriver_mac64/chromedriver"
USER_AGENT_LIST = ['Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
                    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:72.0) Gecko/20100101 Firefox/72.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
                    ]


class AjioLvSpider(scrapy.Spider):
    name = "ajio_lv"
    handle_httpstatus_list = [403]
    start_urls = [
        "https://www.ajio.com/s/fengshui-4720-51871"
    ]

    def __init__(self):
        self.conn = pymongo.MongoClient(
            "localhost",
            27017
        )
        db = self.conn["ajio_scrapy_db"]
        self.collection = db["fengshui_lv"]

    def get_chrome_driver(self, headless_flag):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        if headless_flag:
            # in case you want headless browser
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--start-maximized")
            # chrome_options.add_experimental_option('prefs', {'headers': headers}) # if you want to add custom header
            chrome_options.add_argument("user-agent={}".format(random.choice(USER_AGENT_LIST)))
            driver = webdriver.Chrome(options=chrome_options) 
        else:
            # in case  you want to open browser
            chrome_options = Options()
            # chrome_options.add_experimental_option('prefs', {'headers': headers}) # if you want to add custom header
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("user-agent={}".format(random.choice(USER_AGENT_LIST)))
            chrome_options.headless = False
            driver = webdriver.Chrome(options=chrome_options)

        return driver
    
    def scroll_to_bottom(self, driver):
        # Scroll to the bottom of the page dynamically
        prev_scroll_height = 0
        scroll_attempts = 0

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for a short period to allow content to load
            time.sleep(2)
            
            new_scroll_height = driver.execute_script("return document.body.scrollHeight;")
            
            if new_scroll_height == prev_scroll_height:
                scroll_attempts += 1
                if scroll_attempts >= 3:  # You can adjust the threshold as needed
                    break  # Stop scrolling if no new content after a few attempts
            else:
                scroll_attempts = 0  # Reset the attempts if new content is loaded
                prev_scroll_height = new_scroll_height

    def parse(self, response):
        if response.status == 403:
            self.logger.warning("Status 403 - but chill we are handling using selenium driver.")

        driver = self.get_chrome_driver(headless_flag=False)
        driver.get(response.url)
        time.sleep(2)

        self.scroll_to_bottom(driver)
        
        items = AjioScrapyItem_LV()

        # Extract data using Selenium and yield items
        all_cards = driver.find_elements(By.CSS_SELECTOR, ".item")

        for card in all_cards:
            try:
                product_name = card.find_element(By.CSS_SELECTOR, ".nameCls").text
            except Exception as e:
                product_name = ''
            try:
                product_price = card.find_element(By.CSS_SELECTOR, ".price").text
            except Exception as e:
                product_price = ''
            try:
                product_original_price = card.find_element(By.CSS_SELECTOR, ".orginal-price").text
            except Exception as e:
                product_original_price = ''
            try:
                product_discount_percentage = card.find_element(By.CSS_SELECTOR, ".discount").text
            except Exception as e:
                product_discount_percentage = ''
            try:
                product_brand = card.find_element(By.CSS_SELECTOR, ".brand").text
            except Exception as e:
                product_brand = ''
            try:
                product_image_url = card.find_element(By.XPATH, "/html/body/div[1]/div/div/div[2]/div/div/div/div[2]/div[2]/div[3]/div[1]/div/div/a/div/div[1]/div[1]/img").get_attribute("src")
            except Exception as e:
                product_image_url = ''
            try:
                product_url = card.find_element(By.CSS_SELECTOR, ".item a").get_attribute("href")
            except Exception as e:
                product_url = ''

            items["product_name"] = product_name
            items["product_price"] = product_price
            items["product_original_price"] = product_original_price
            items["product_discount_percentage"] = product_discount_percentage
            items["product_brand"] = product_brand
            items["product_image_url"] = product_image_url
            items["product_url"] = product_url

            self.collection.insert_one(dict(items))

            yield items

        driver.quit()
