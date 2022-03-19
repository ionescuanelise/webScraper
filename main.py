import csv
from time import sleep
from pathlib import Path

import sentiment

import nltk

from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

import re

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions

nltk.download("stopwords")
chachedWords = stopwords.words('english')


def tokenize(txt):
    txt = txt.lower()
    text_tokens = re.sub(r"[^\w\s]|_", " ", txt).split()
    return text_tokens


def remove_stopwords(input_tokens):
    return [token for token in input_tokens if token not in chachedWords]


def apply_stemming(input_tokens):
    ps = PorterStemmer()
    return [ps.stem(token) for token in input_tokens]


def create_webdriver_instance():
    driver = webdriver.Chrome()
    return driver


def find_search_input_and_enter_criteria(search_term, driver):
    url = 'https://twitter.com/search'
    driver.get(url)
    driver.maximize_window()
    sleep(5)

    search_input = driver.find_element_by_xpath('//input[@aria-label="Search query"]')
    search_input.send_keys(search_term)
    search_input.send_keys(Keys.RETURN)
    sleep(5)
    return True


def change_page_sort(tab_name, driver):
    """Options for this program are `Latest` and `Top`"""
    tab = driver.find_element_by_link_text(tab_name)
    tab.click()
    # xpath_tab_state = f'//a[contains(text(),\"{tab_name}\") and @aria-selected=\"true\"]'


def generate_tweet_id(tweet):
    return ''.join(tweet)


def scroll_down_page(driver, last_position, num_seconds_to_load=2, scroll_attempt=0, max_attempts=60):
    end_of_scroll_region = False
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(num_seconds_to_load)
    curr_position = driver.execute_script("return window.pageYOffset;")
    if curr_position == last_position:
        if scroll_attempt < max_attempts:
            end_of_scroll_region = True
        else:
            scroll_down_page(last_position, curr_position, scroll_attempt + 1)
    last_position = curr_position
    return last_position, end_of_scroll_region


def save_tweet_data_to_csv(records, filepath, mode='a+'):
    header = ['coin_type', 'url', 'title', 'content', 'published_at', 'source', 'sentiment', 'text']
    with open(filepath + '_top_news.csv', mode=mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(header)
        if records:
            writer.writerow(records)


def collect_all_tweets_from_current_view(driver, lookback_limit=25):
    page_cards = driver.find_elements_by_xpath('//article[@data-testid="tweet"]')
    if len(page_cards) <= lookback_limit:
        return page_cards
    else:
        return page_cards[-lookback_limit:]


def extract_data_from_current_tweet_card(card, search_term, count):
    try:
        source = "https://twitter.com/" + card.find_element_by_xpath('.//span[contains(text(), "@")]').text
        handle = card.find_element_by_xpath('.//span[contains(text(), "@")]').text
    except exceptions.NoSuchElementException:
        source = "https://twitter.com/"
    try:
        published_at = card.find_element_by_xpath('.//time').get_attribute('datetime')
    except exceptions.NoSuchElementException:
        return
    try:
        _comment = card.find_element_by_xpath('.//div[2]/div[2]/div[1]').text
    except exceptions.NoSuchElementException:
        _comment = ""
    try:
        _responding = card.find_element_by_xpath('.//div[2]/div[2]/div[2]').text
    except exceptions.NoSuchElementException:
        _responding = ""
    tweet_text = _comment + _responding
    text = tweet_text

    title = "top tweet about " + search_term.split(' ')[0] + " news"
    url = "https://twitter.com/search?q=" + search_term + "&src=typed_query/" + handle + str(count)
    sentiment_score = str(sentiment.get_polarity(tweet_text))
    words = apply_stemming(remove_stopwords(tokenize(tweet_text)))
    preprocessed_text = " ".join(words)
    coin_type = str(search_term)

    tweet = (coin_type, url, title, preprocessed_text, published_at, source, sentiment_score, text)
    return tweet


def main(search_term, filepath, no_of_tweets, page_sort='Latest'):
    save_tweet_data_to_csv(None, filepath, 'w')  # create file for saving records
    last_position = None
    end_of_scroll_region = False
    unique_tweets = set()

    count = 0

    driver = create_webdriver_instance()

    search_found = find_search_input_and_enter_criteria(search_term, driver)
    if not search_found:
        return

    change_page_sort(page_sort, driver)

    while not end_of_scroll_region and count < no_of_tweets:
        cards = collect_all_tweets_from_current_view(driver)
        for card in cards:
            try:
                tweet = extract_data_from_current_tweet_card(card, search_term, count)
            except exceptions.StaleElementReferenceException:
                continue
            if not tweet:
                continue
            tweet_id = generate_tweet_id(tweet)
            if tweet_id not in unique_tweets:
                count += 1
                unique_tweets.add(tweet_id)
                save_tweet_data_to_csv(tweet, filepath)
        last_position, end_of_scroll_region = scroll_down_page(driver, last_position)
    driver.quit()


if __name__ == '__main__':
    path = './data/'
    Path(path).mkdir(exist_ok=True)
    with open('coins_list.txt', 'r') as file:
        terms = file.read().rstrip()

    for term in terms:
        main(term, path + term, 500000)


