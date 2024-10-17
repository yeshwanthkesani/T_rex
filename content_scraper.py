import pandas as pd
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common import TimeoutException,  NoSuchElementException, StaleElementReferenceException, NoSuchWindowException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import random
import time 
from fake_useragent import UserAgent
from bs4 import BeautifulSoup


# random fake agent

user_agents = []
ua = UserAgent()
for i in range(10):
    user = ua.random
    user_agents.append(user)


# Initialize an empty DataFrame
def get_webdriver():
    random_user_agent = random.choice(user_agents)
    options = Options()
    options.add_argument(f"user-agent={random_user_agent}") # selecting the random user
    options.page_load_strategy = 'eager'  # 'none' can be risky, 'eager' ensures content is loaded
    options.add_argument('--ignore-certificate-errors')
    #options.add_argument('--headless')  # Set to True to run in headless mode
    options.add_argument('--log-level=3')
    options.add_argument('--disable-gpu')  # Disabling GPU in headless mode
    options.add_argument('--disable-infobars')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Disable loading images for faster scraping
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options= options)
    return driver


def extract_content_from_url(driver, url):
    try:
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Adding manual sleep to give time for page elements to load
        time.sleep(5)  # Wait for 5 seconds to ensure full page load
        
        # Get the page source and parse it with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract the content within 'body_content'
        content_div = soup.find('div', class_='body__content')
        if content_div is None:
            print(f"Error: body_content div not found on {url}")
            return "Content not available (No body content found)"
        
        # Extract all paragraph text from the content
        paragraphs = content_div.find_all('p')
        content = " ".join([para.get_text() for para in paragraphs if para.get_text().strip()])

        # Log the extracted content for debugging
        print(f"Extracted content from {url}: {content[:500]}...")  # Limit the output to first 500 characters for readability
        return content

    except TimeoutException:
        print(f"Timeout: Could not load content from {url}")
        return "Content not available (Timeout)"
    except NoSuchElementException:
        print(f"Error: Could not find content on page {url}")
        return "Content not available (No element found)"
    except Exception as e:
        print(f"Error loading {url}: {str(e)}")
        return "Content not available (Unknown error)"


def extract_content_for_csv(csv_filename, output_csv):
    # Read the CSV file containing the headlines and URLs
    df = pd.read_csv(csv_filename)
    
    # Add a new column for the content
    if 'content' not in df.columns:
        df['content'] = ""

    # Initialize the WebDriver
    driver = get_webdriver()

    for index, row in df.iterrows():
        url = row['url']
        print(f"Extracting content for URL: {url}")
        
        # Extract content from the article URL using BeautifulSoup
        content = extract_content_from_url(driver, url)
        
        # Add the extracted content to the DataFrame
        df.at[index, 'content'] = content
    
    # Close the WebDriver
    driver.quit()

    # Save the updated DataFrame back to CSV
    df.to_csv(output_csv, index=False)
    print(f"Updated CSV saved as: {output_csv}")
csv_filename = "headlines_dynamic.csv"  # CSV with 'headline' and 'url'
output_csv = "nvda_headlines_with_content.csv"  # CSV to save the result

# Extract content for each URL and save it
extract_content_for_csv(csv_filename, output_csv)

