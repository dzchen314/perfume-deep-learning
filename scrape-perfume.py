from bs4 import BeautifulSoup
import os
import time
import requests
import json
import glob

#location for the reviews
BASE_URL = 'http://www.basenotes.net/fragrancereviews/page/{0}'
session = requests.Session()
HEADERS = {
    'user-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36')
}
DATA_DIR = 'data'
FILENAME = 'perfume-data'

class Scraper():
    """Scraper for basenotes.com"""

    def __init__(self, pages_scraped=(1,1)):
        self.pages_scraped = pages_scraped
        self.session = requests.Session()
        self.est_reviews = (pages_scraped[1] + 1 - pages_scraped[0]) * 30 #there are 30 reviews per page
        self.review_count = 0
        self.start_time = time.time()

    def scrape_site(self):
        for page in range(self.pages_scraped[0], self.pages_scraped[1] + 1):
            self.scrape_page(BASE_URL.format(page))
        print('Scrape finished...')
        self.condense_data()

    def scrape_page(self, page_url, review_count=0, retry_count=0):
        scrape_data = []
        try:
            response = self.session.get(page_url, headers=HEADERS)
        except:
            retry_count += 1
            if retry_count <= 3:
                self.session = requests.Session()
                self.scrape_page(page_url, review_count, retry_count)
            else:
                raise

        soup = BeautifulSoup(response.content, 'html.parser')
        reviews = soup.find_all('div', {'class': 'reviewblurb'})[0:]
        for review in reviews:
            review_url = review.find('a')['href']
            #parse perfume name and maker
            split_name = str(review.find('a')).split('>')
            
            self.review_count += 1
            split = split_name[1][0:-3].split(' by ')
            perfume_name = split[0]
            perfume_maker = split[1]
            
            #parse review
            split_review = str(review).split('</h2>')
            review_text = split_review[len(split_review)-1][0:-6]
            
            #right now I am pulling name, maker, and review text. I plan to add rating and scents
            review_data = {
            'perfume': perfume_name,
            'maker': perfume_maker,
            'review': review_text
            }
             
            scrape_data.append(review_data)
            self.update_scrape_status()
        self.save_data(scrape_data)

    def save_data(self, data):
        filename = '{}/{}_{}.json'.format(DATA_DIR, FILENAME, time.time())
        try:
            os.makedirs(DATA_DIR)
        except OSError:
            pass
        with open(filename, 'w') as fout:
            json.dump(data, fout)

    def condense_data(self):
        print('Condensing Data...')
        condensed_data = []
        all_files = glob.glob('{}/*.json'.format(DATA_DIR))
        for file in all_files:
            with open(file, 'rb') as fin:
                condensed_data += json.load(fin)
        print(len(condensed_data))
        filename = '{}.json'.format(FILENAME)
        with open(filename, 'w') as fout:
            json.dump(condensed_data, fout)

    def update_scrape_status(self):
        elapsed_time = round(time.time() - self.start_time, 2)
        time_remaining = round((self.est_reviews - self.review_count) * (self.review_count / elapsed_time), 2)
        print('{0}/{1} reviews pulled | {2}s elapsed | {3}s remain\r'.format(
            self.review_count, self.est_reviews, elapsed_time, time_remaining))

if __name__ == '__main__':
    pages = (1, 1)
    perfume_scraper = Scraper(pages_scraped = pages)

    perfume_scraper.scrape_site()
