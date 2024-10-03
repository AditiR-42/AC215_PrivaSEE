# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from playwright.async_api import async_playwright

# Base URL of the page (changing only the page number)
base_url = 'https://edit.tosdr.org/services?page='
annotate_base_url = 'https://edit.tosdr.org'

# Function to scrape services and ratings
def scrape_services():
    services = []
    ratings = []

    for page_num in range(1, 416):
        url = base_url + str(page_num)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        services_table = soup.find('table')

        for row in services_table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) > 1:
                service_name = cols[0].get_text(strip=True)
                rating = cols[1].get_text(strip=True)
                services.append(service_name)
                ratings.append(rating)

        time.sleep(random.uniform(1, 10))  # Random sleep

    df_services = pd.DataFrame({'Service': services, 'Rating': ratings})
    df_services.to_csv('services_and_ratings.csv', index=False)
    print("Services and ratings saved to 'services_and_ratings.csv'.")

# Function to scrape annotate URLs
def scrape_annotate_urls():
    annotate_urls = []

    for page_num in range(1, 2):
        url = base_url + str(page_num)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        services_table = soup.find('table')

        for row in services_table.find_all('tr'):
            annotate_button = row.find('a', string='Annotate')
            if annotate_button:
                annotate_link = annotate_button['href']
                full_annotate_url = annotate_base_url + annotate_link
                annotate_urls.append(full_annotate_url)

    # Save annotate URLs to CSV
    df_annotate_urls = pd.DataFrame({'Annotate URL': annotate_urls})
    df_annotate_urls.to_csv('annotate_urls.csv', index=False)
    print("Annotate URLs saved to 'annotate_urls.csv'.")

# Function to scrape annotation details
def scrape_annotation_details(annotate_url):
    response = requests.get(annotate_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    highlighted_texts = []
    annotations = []

    for annotation_item in soup.find_all('div', class_='annotation'):
        highlighted = annotation_item.find('mark')
        if highlighted:
            highlighted_texts.append(highlighted.get_text(strip=True))
        annotation_text = annotation_item.find('div', class_='annotation-text').get_text(strip=True)
        annotations.append(annotation_text)

    df_annotations = pd.DataFrame({'Highlighted Text': highlighted_texts, 'Annotation': annotations})
    df_annotations.to_csv('annotations.csv', index=False)
    print("Annotations saved to 'annotations.csv'.")

# Function to scrape cases
def scrape_cases():
    driver_path = '/path/to/chromedriver'  # Update this path
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service)
    url = 'https://edit.tosdr.org/cases'

    driver.get(url)
    time.sleep(3)  # Adjust the sleep time as needed
    page_source = driver.page_source
    driver.quit()

    soup = BeautifulSoup(page_source, 'html.parser')
    case_titles = []
    for row in soup.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 0:
            title = cols[0].get_text(strip=True)
            case_titles.append(title)

    # Save case titles to CSV
    df_cases = pd.DataFrame({'Case Title': case_titles})
    df_cases.to_csv('case_titles.csv', index=False)
    print("Case titles saved to 'case_titles.csv'.")

# Async function to scrape topics and their cases
async def scrape_cases_for_topics():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto('https://edit.tosdr.org/topics')
        await page.wait_for_selector('tr')

        titles = await page.locator('tr td:nth-child(2) a').all_inner_texts()
        links = await page.locator('tr td:nth-child(2) a').evaluate_all('elements => elements.map(e => e.href)')

        all_cases = []
        for title, link in zip(titles, links):
            await page.goto(link)
            await page.wait_for_selector('div.card-inline')
            case_titles = await page.locator('div.card-inline td a').all_inner_texts()
            case_links = await page.locator('div.card-inline td a').evaluate_all('elements => elements.map(e => e.href)')
            for case_title, case_link in zip(case_titles, case_links):
                all_cases.append({'Topic': title, 'Topic Link': link, 'Case': case_title, 'Case Link': case_link})

        await browser.close()
        df_cases = pd.DataFrame(all_cases)
        df_cases.to_csv('cases_by_topic.csv', index=False)
        print("Cases by topic saved to 'cases_by_topic.csv'.")
        return df_cases

# Main function to run the async scraping
async def main():
    # Uncomment the desired function to run
    scrape_services()
    scrape_annotate_urls()
    # Uncomment and provide a valid annotate URL to scrape annotations
    # annotate_url = 'https://edit.tosdr.org/services/1570/annotate'
    # scrape_annotation_details(annotate_url)
    await scrape_cases_for_topics()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())