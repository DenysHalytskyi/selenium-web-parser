"""The script collects product data and stores it in a Postgres database."""

from load_django import *
from parser_app.models import *
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import time
from pprint import pprint


service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
spec = {}

try:
    driver.get("https://brain.com.ua/")     # 1
    driver.maximize_window()

    wait = WebDriverWait(driver, 15)

    inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"header-search-form")]//input[@type="search"]')))

    for i in inputs:
        if i.is_displayed():
            search_input = i
            break

    search_input.click()
    search_input.clear()
    search_input.send_keys('Apple iPhone 15 128GB Black')
    search_input.send_keys(Keys.ENTER)


    first_iphone = wait.until(EC.element_to_be_clickable((By.XPATH, '(//div[contains(@class,"br-pp-desc")]//a)[1]')))    # 4
    first_iphone.click()

    product_info = {}
    images_list = []

    try:    #Full name
        full_name = driver.find_element(By.XPATH, '//div[@id="br-characteristics"]//span[contains(@class, "product-clean-name")]').text.strip()
        product_info['full_name'] = full_name

    except NoSuchElementException as e:
        product_info['full_name'] = None


    try:    #product code
        load_product_code = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="br-pr-1"]//span[contains(@class, "br-pr-code-val")]')))
        product_code = load_product_code.get_attribute("textContent").strip()
        product_info['product_code'] = product_code
    except NoSuchElementException as e:
        product_info['product_code'] = None


    try:    #main price
        main_price = driver.find_element(By.XPATH, '//div[contains(@class, "pr-op")]//span').text.replace(' ', '')
        product_info['main_price'] = int(main_price)
    except NoSuchElementException as e:
        product_info['main_price'] = None


    try:    #red price
        red_price = driver.find_element(By.XPATH, '//div[contains(@class, "pr-np")]//span').text.replace(' ', '')
        product_info['red_price'] = int(red_price)
    except NoSuchElementException as e:
        product_info['red_price'] = None


    try:    #review count
        review = driver.find_element(By.XPATH, '//div[@id="br-pr-1"]//a[contains(@class, "brackets-reviews")]').text
        review_count = ''.join(filter(str.isdigit, review))
        product_info['review_count'] = int(review_count)
    except NoSuchElementException as e:
        product_info['review_count'] = None


    #images
    images = driver.find_elements(By.XPATH, '//div[contains(@class, "br-image-links")]//img')

    for image in images:
        src = image.get_attribute('src')
        if src:
            images_list.append(src)

    if not images_list:
        product_info['images'] = None
    else:
        product_info['images'] = images_list


    try:    #characteristics
        wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "br-pr-chr-item")]')))     # 1 of 11
        characteristics_block = driver.find_elements(By.XPATH, '//div[contains(@class, "br-pr-chr-item")]//div[span[2]]')    #1 of 40
        for item in characteristics_block:
            spans = item.find_elements(By.TAG_NAME, 'span')

            if len(spans) >= 2:
                key = spans[0].get_attribute('textContent').strip()
                value = spans[1].get_attribute('textContent').strip()

                if key:
                    spec[key] = " ".join(value.split())

        product_info['characteristics'] = spec

    except NoSuchElementException as e:
        product_info['characteristics'] = None


    try:
        product_info['color'] = spec['Колір']
    except AttributeError as e:
        product_info['color'] = None
    try:
        product_info['memory'] = spec["Вбудована пам'ять"]
    except AttributeError as e:
        product_info['memory'] = None
    try:
        product_info['producer'] = spec['Виробник']
    except AttributeError as e:
        product_info['producer'] = None
    try:
        product_info['diagonal'] = spec['Діагональ екрану']
    except AttributeError as e:
        product_info['diagonal'] = None
    try:
        product_info['resolution'] = spec['Роздільна здатність екрану']
    except AttributeError as e:
        product_info['resolution'] = None


    pprint(product_info, sort_dicts=False)


    data_to_save = {
        "full_name": product_info["full_name"],
        "product_code": product_info["product_code"],
        "main_price": product_info["main_price"],
        "red_price": product_info["red_price"],
        "color": product_info["color"],
        "memory": product_info["memory"],
        "producer": product_info["producer"],
        "screen_diagonal": product_info["diagonal"],
        "display_resolution": product_info["resolution"],
        "characteristics": product_info["characteristics"],
        "image": product_info["images"],
        "review_count": product_info["review_count"]
    }

    try:
        obj, created = Product.objects.get_or_create(**data_to_save)
        status = "created" if created else "already exists"
        print(f"{obj.full_name} ({obj.product_code}) ({status})")
    except Product.MultipleObjectsReturned:
        print("Multiple products found")

except NoSuchElementException as e:
    print(f"Error + {e}")
except Exception as e:
    print(f"Error + {e}")


finally:
    driver.quit()
