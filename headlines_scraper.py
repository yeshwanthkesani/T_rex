import os
import random
import time 
import pandas as pd 
from selenium import webdriver
from selenium.common import TimeoutException,  NoSuchElementException, StaleElementReferenceException, NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import csv


# intitializing fake agent

user_agents = []
ua = UserAgent()
for i in range(10):
    user = ua.random
    user_agents.append(user)


def get_webdriver():
    random_user_agent = random.choice(user_agents)
    options = Options()
    options.add_argument(f"user-agent={random_user_agent}") # selecting the random user
    options.page_load_strategy = 'eager'  # 'none' can be risky, 'eager' ensures content is loaded
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--headless')  # Set to True to run in headless mode
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





def save_pd(headline, link, date, df, csv_filename="headlines_dynamic.csv"):
    """Function to append data to DataFrame and save to CSV."""
    
    # Create a DataFrame for the new row
    new_row = pd.DataFrame({
        'headline': [headline],
        'url': [link],
        'date': [date]
    })
    
    # Append the new row to the main DataFrame
    df = pd.concat([df, new_row], ignore_index=True)

    # Save the updated DataFrame to CSV
    df.to_csv(csv_filename, index=False)

    return df



def extract_headlines(driver, url, df):
    """Extract headlines from given URL"""
    headlines_data = []
    driver.get(url)
    while True:
        try:
            
            
            #print("Waiting for search result items to load...")
            results_container = safe_find_element(driver, By.CLASS_NAME, 'search-results__results-items')
            if results_container:
                #print("Search results container found.")
            else:
                #print("Search results container not found.")
            #print("Search results loaded.")
            article_elements = driver.find_elements(By.CLASS_NAME, 'search-results__item--with-topics')
            if not article_elements:  # Check if no articles are found
                #print("No articles found on this page.")
                break
            #print(f"Found {len(article_elements)} article elements.")
    
            for i, article in enumerate(article_elements):
                try:
                    #print(f"Processing article {i + 1}...")
                    # Extract headline text
                    headline = article.find_element(By.CLASS_NAME, 'search-results__header-title').text
                    #print(f"Headline {i + 1}: {headline}")
    
                    # Extract URL
                    link = article.get_attribute('href')
                    #print(f"URL {i + 1}: {link}")
    
                    # Extract date
                    date = article.find_element(By.CLASS_NAME, 'search-results__date').text
                    #print(f"Date {i + 1}: {date}")
                    df = save_pd(headline, link, date, df)
    
                    # Store the data
                    headlines_data.append({
                        'headline': headline,
                        'url': link,
                        'date': date
                    })
                except NoSuchElementException:
                    #print("Could not find headline, URL, or date for one article, skipping.")
            if not go_to_next_page(driver):
                #print("No more pages left.")
                break
        except TimeoutException:
            #print("Timeout while waiting for headlines to load.")
            break
        except NoSuchElementException:
            #print("Could not find headline elements.")
            break
        
    #print("Finished extracting headlines.")
        
    return headlines_data, df

def go_to_next_page(driver):
    """Function to go to the next page"""
    try:
        #print("Checking for 'Next' button...")
        
        # Find the 'Next' button
        next_button = driver.find_element(By.CLASS_NAME, 'pagination__next')

        # Scroll to the button to ensure it's in view
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)

        # Close potential overlays (like cookie consent banners)
        try:
            # Example: Handle cookie consent banner or modal (adjust the selector as needed)
            cookie_banner = driver.find_element(By.ID, "cookie-consent-banner")  # Example ID
            close_button = cookie_banner.find_element(By.TAG_NAME, 'button')
            close_button.click()
            #print("Closed cookie consent banner.")
        except NoSuchElementException:
            #print("No cookie consent banner found, proceeding with pagination.")

        # Click the 'Next' button
        if next_button.is_enabled():
            #print("Found 'Next' button, navigating to the next page...")
            next_button.click()
            time.sleep(3)  # Add some delay to ensure the next page loads completely
            return True
        else:
            #print("'Next' button is not enabled.")
            return False

    except NoSuchElementException:
        #print("No 'Next' button found.")
        return False
    except ElementClickInterceptedException:
        #print("Error: Could not click 'Next' button, element is obstructed.")
        return False




""" you can change the new data which you want to collect in the link"""


if __name__ == "__main__":
    # Initialize WebDriver
    driver = get_webdriver()

    # Target URL (replace with the actual URL containing headlines)
    url = "https://www.nasdaq.com/search?q=nvda%20news&page=1&langcode=en"  # Replace nvda with other stock symbol
    columns = ['headline', 'url', 'date']
    df = pd.DataFrame(columns=columns)

    # Extract headlines
    headlines, df = extract_headlines(driver, url, df)

    # Print or save the extracted headlines
    if headlines:
        for i, headline_data in enumerate(headlines):
            print(f"Headline {i + 1}: {headline_data['headline']}")
            print(f"URL: {headline_data['url']}")
    else:
        print("No headlines found.")
