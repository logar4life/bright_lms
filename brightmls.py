import time
import csv
import os
import pandas as pd
import hashlib
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException
import gspread
from google.oauth2.service_account import Credentials
import json

# === Credentials ===
USERNAME = "najibm1983"
PASSWORD = "Logar4life!"

# === URLs ===
LOGIN_URL = "https://login.brightmls.com/login"
SEARCH_URL = "https://matrix.brightmls.com/Matrix/Search/ResidentialSale/Residential"

# === File paths ===
DATA_HASH_FILE = "data_hash.txt"

# Google Sheets setup
GSHEET_ID = "1ldE3Jz6N0ZhsgSq4S43zjjEAMlTFGTP65JmnFSvI7Js"  # <-- Set your Google Sheet ID
GSHEET_NAME = "Sheet1"  # <-- Set your Google Sheet tab name

import warnings

# Removed save_data_to_csv function

service_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
if service_json:
    with open("service.json", "w") as f:
        f.write(service_json)

def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    if not os.path.isfile("service.json"):
        warnings.warn("service.json not found. Google Sheets saving will be skipped.")
        return None
    creds = Credentials.from_service_account_file("service.json", scopes=scopes)
    client = gspread.authorize(creds)
    return client

def save_data_to_gsheet(data, timestamp):
    """Save data to Google Sheet without headers or column names, just raw values."""
    if not data:
        return False
    # Add timestamp to each row
    for row in data:
        row['Timestamp'] = timestamp

    client = get_gsheet_client()
    if client is None:
        print("⚠️ Google Sheets client not available. Skipping Google Sheets save.")
        return False
    sheet = client.open_by_key(GSHEET_ID).worksheet(GSHEET_NAME)

    # Prepare rows to append (no headers, just values in the order of the dict)
    rows_to_append = []
    for row in data:
        # Just take the values, in the order they appear in the dict
        row_data = list(row.values())
        rows_to_append.append(row_data)
    # Append rows (no header update)
    sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
    print(f"✅ Data appended to Google Sheet (no headers)")
    return True

def get_data_hash(data):
    """Generate a hash of the data to detect changes"""
    data_str = str(data)
    return hashlib.md5(data_str.encode()).hexdigest()

def save_data_hash(hash_value):
    """Save the current data hash to file"""
    with open(DATA_HASH_FILE, 'w') as f:
        f.write(hash_value)

def load_data_hash():
    """Load the previous data hash from file"""
    try:
        with open(DATA_HASH_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None



def scrape_data(driver, wait, max_retries=3):
    """Scrape data from the results table, with retry for stale element errors and robust header/row extraction. Always use headerless mode."""
    for attempt in range(max_retries):
        try:
            specific_xpath = "/html/body/form/div[3]/div[7]/table/tbody/tr/td/div[2]/div[3]/div[3]/div/div/div[1]/table"
            try:
                table_element = driver.find_element(By.XPATH, specific_xpath)
                print("✅ Found table using specific XPath")
            except Exception as e:
                print(f"❌ Could not find table using specific XPath: {e}")
                table_element = driver.find_element(By.TAG_NAME, "table")
                print("✅ Found table using fallback method")

            table_html = table_element.get_attribute('outerHTML')
            soup = BeautifulSoup(table_html, 'html.parser')

            # Always treat as headerless: do not extract headers from table
            all_trs = soup.find_all('tr')
            rows = []
            max_cols = 0
            for tr in all_trs:
                cells = tr.find_all(['td', 'th'])
                if cells:
                    row_data = []
                    price_change_type = None
                    price_change_title = None
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        # Only check for price up/down images
                        img = cell.find('img')
                        if img and img.get('src'):
                            src = img['src']
                            title = img.get('title') or img.get('data-original-title') or ''
                            if 'pricedown' in src:
                                price_change_type = 'down'
                                price_change_title = title or 'Price Decrease'
                            elif 'priceup' in src:
                                price_change_type = 'up'
                                price_change_title = title or 'Price Increase'
                        row_data.append(text)
                    # Add price change info as extra columns
                    if price_change_type:
                        row_data.append(price_change_type)
                        row_data.append(price_change_title)
                    else:
                        row_data.append('')
                        row_data.append('')
                    if any(cell.strip() for cell in row_data):
                        rows.append(row_data)
                        if len(row_data) > max_cols:
                            max_cols = len(row_data)
            # Generate headers as Column_1, Column_2, ...
            headers = [f'Column_{i+1}' for i in range(max_cols)]
            print(f"Extracted {len(rows)} rows.")
            data = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = value
                    else:
                        row_dict[f'Column_{i+1}'] = value
                data.append(row_dict)
            return data, headers
        except StaleElementReferenceException as e:
            print(f"⚠️ StaleElementReferenceException on attempt {attempt+1}, retrying...")
            time.sleep(2)
            continue
        except Exception as e:
            print(f"❌ Error scraping data: {e}")
            return [], []
    print("❌ Failed to scrape data after retries due to stale elements.")
    return [], []

def scroll_to_element(driver, element):
    """Scroll to element and wait for it to be clickable"""
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
    time.sleep(2)

def safe_click(driver, wait, element):
    """Safely click element with scrolling and waiting"""
    scroll_to_element(driver, element)
    wait.until(EC.element_to_be_clickable(element))
    driver.execute_script("arguments[0].click();", element)

def perform_search(driver, wait):
    """Perform the search and get results"""
    try:
        # Step 1: Navigate to search page
        driver.get(SEARCH_URL)
        time.sleep(10)

        # Step 2: Click "Select All" - with proper scrolling
        select_all = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Select All')]")))
        safe_click(driver, wait, select_all)
        time.sleep(2)

        # Step 3: Select "Detached"
        detached_option = wait.until(EC.presence_of_element_located((By.XPATH, "//option[@value='27007' and @title='Detached']")))
        scroll_to_element(driver, detached_option)
        driver.execute_script("arguments[0].click();", detached_option)
        time.sleep(2)

        # Step 4: Scroll to middle
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(2)

        # Step 5: Click "Results" button
        results_button = wait.until(EC.element_to_be_clickable((By.ID, "m_ucSearchButtons_m_lbSearch")))
        safe_click(driver, wait, results_button)
        time.sleep(10)

        return True
        
    except Exception as e:
        print(f"❌ Error performing search: {e}")
        return False

def scrape_all_pages(driver, wait, max_pages=200):
    """Scrape up to max_pages of the results table and save each page's data in real time to Google Sheets."""
    all_data = []
    headers = None
    page_num = 1
    
    # Import the stop flag from main module
    try:
        import main
        stop_flag = main.stop_scraper
    except:
        stop_flag = False
    
    while page_num <= max_pages:
        # Check if we should stop
        try:
            import main
            if main.stop_scraper:
                print("🛑 Stop signal received, stopping scraper...")
                break
        except:
            pass
            
        print(f"\n🔄 Scraping page {page_num}...")
        data, page_headers = scrape_data(driver, wait)
        if not data:
            print(f"❌ No data found on page {page_num}")
            break
        if headers is None:
            headers = page_headers
        all_data.extend(data)
        # Save this page's data immediately
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # save_data_to_csv(data, timestamp)  # Removed CSV saving
        save_data_to_gsheet(data, timestamp)
        # Find the pager and the Next link
        try:
            pager = driver.find_element(By.CSS_SELECTOR, 'span.pagingLinks')
            next_link = None
            for a in pager.find_elements(By.TAG_NAME, 'a'):
                if a.text.strip().lower() == 'next':
                    next_link = a
                    break
            if next_link and next_link.is_enabled() and page_num < max_pages:
                try:
                    driver.execute_script("arguments[0].click();", next_link)
                except StaleElementReferenceException:
                    print("⚠️ Stale pager element, retrying next page click...")
                    time.sleep(2)
                    continue
                time.sleep(5)  # Wait for next page to load
                page_num += 1
            else:
                print("✅ No more pages or reached max page limit.")
                break
        except StaleElementReferenceException:
            print("⚠️ Stale pager element, retrying...")
            time.sleep(2)
            continue
        except Exception as e:
            print(f"❌ Pager navigation error: {e}")
            break
    return all_data, headers

def run_brightmls_scraper():
    """Run the scraping process and return a result dictionary."""
    # Setup Chrome driver with enhanced headless options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')  # or '--headless' for older Chrome
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument("--window-size=1920,1080")  # Set window size for consistent rendering
    options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
    options.add_argument("--disable-web-security")  # Disable web security
    options.add_argument("--allow-running-insecure-content")  # Allow insecure content
    options.add_argument("--disable-features=VizDisplayCompositor")  # Disable display compositor
    options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Hide automation
    options.add_experimental_option('useAutomationExtension', False)  # Disable automation extension
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,  # Disable notifications
        "profile.default_content_settings.popups": 0,  # Disable popups
        "profile.managed_default_content_settings.images": 2  # Disable images
    })
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    result = {
        'success': False,
        'message': '',
        'row_count': 0,
        'new_data': False,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    try:
        # Initial login
        print("🔄 Logging in...")
        driver.get(LOGIN_URL)
        time.sleep(3)
        driver.find_element(By.ID, "username").send_keys(USERNAME)
        time.sleep(1)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        time.sleep(1)
        driver.find_element(By.ID, "password").send_keys(Keys.TAB)
        time.sleep(2)
        login_button = driver.find_element(By.XPATH, "//button[@type='submit' and text()='LOG IN']")
        login_button.click()
        time.sleep(10)
        print("✅ Login successful")

        print(f"\n🔄 Starting data collection at {result['timestamp']}")
        # Perform search
        if not perform_search(driver, wait):
            result['message'] = "❌ Search failed"
            return result
        # Scrape all pages and save in real time
        data, headers = scrape_all_pages(driver, wait)
        if not data:
            result['message'] = "❌ No data found"
            return result
        # Generate hash of current data
        current_hash = get_data_hash(data)
        previous_hash = load_data_hash()
        if current_hash == previous_hash:
            result['message'] = "ℹ️ No new data found - data unchanged"
            result['row_count'] = len(data)
        else:
            print("🆕 New data detected!")
            # Save new hash
            save_data_hash(current_hash)
            print(f"✅ New data saved with {len(data)} rows")
            result['message'] = f"✅ New data saved with {len(data)} rows"
            result['row_count'] = len(data)
            result['new_data'] = True
        result['success'] = True
        return result
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted by user")
        result['message'] = "🛑 Script interrupted by user"
        return result
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        result['message'] = f"❌ Fatal error: {e}"
        return result
    finally:
        driver.quit()
