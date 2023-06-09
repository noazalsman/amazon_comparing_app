import random
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import time
from models import db, SearchData, User
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'search_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # db.drop_all()  # Drop all existing tables
    db.create_all()

    # Create a shared user if the user table is empty
    if User.query.count() == 0:
        shared_user = User(daily_search_count=0)
        db.session.add(shared_user)
        db.session.commit()


def fetch_product_page_with_args(args):
    return fetch_amazon_search_page(*args)


def fetch_amazon_search_page(query='None', country='com', is_asin=False):
    if query is None:
        return None
    headers = get_headers()
    if not is_asin:
        url = f'https://www.amazon.{country}/s?k={query}'
    else:
        url = f'https://www.amazon.{country}/dp/{query}'
    time.sleep(3) # add a 3 second delay
    response = requests.get(url, headers=headers)
    print("searching...")
    return response.text


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; AS; rv:11.0) like Gecko'
]


def get_headers():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    return headers


def extract_price(page_content, country):
    if page_content is None:
        return None
    soup = BeautifulSoup(page_content, 'html.parser')
    price_element = soup.find('span', {'class': 'a-offscreen'})
    if price_element:
        price = price_element.text.strip()
        price = float(re.sub(r'[^\d.]', '', price))
        print("extracting:", price)
        if country in ['co.uk', 'de']:
            price = convert_to_usd(price, country)
        return price
    return None


def convert_to_usd(price, country):
    conversion_rates = {
        'co.uk': 1.26,  # GBP to USD
        'de': 1.11,  # EUR to USD
    }
    return price * conversion_rates.get(country, 1)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    text = fetch_amazon_search_page(query)

    # Parse the response using BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')

    # Extract the top 10 search results
    search_results = []
    results = soup.find_all('div', {'data-component-type': 's-search-result'})

    for result in results:
        if len(search_results) < 10:
            try:
                # Get the product name
                name = result.find('span', class_='a-size-base-plus a-color-base a-text-normal')

                # Get the product image URL
                image = result.find('img', class_='s-image')

                # Get the product ASIN
                asin = result['data-asin']

                price = result.find('span', class_='a-price-whole')

                # price_symbol = result.find('span', class_='a-price-symbol').text

                rating = result.find('span', class_='a-icon-alt')

                if name:
                    name = name.text
                if image:
                    image = image['src']
                if price:
                    price = price.text.split('.')[0]
                if rating:
                    rating = result.find('span', class_='a-icon-alt').text.split(' ')[0]

                search_results.append({
                    'name': name,
                    'image': image,
                    'asin': asin,
                    'price': price,
                    'rating': rating,
                })

            except (AttributeError, KeyError):
                continue

    # Increment the search count for the shared user and update the last search date
    shared_user = User.query.first()
    if shared_user.last_search_date is None or shared_user.last_search_date.date() < datetime.utcnow().date():
        shared_user.daily_search_count = 1
        shared_user.last_search_date = datetime.utcnow()
    else:
        shared_user.daily_search_count += 1
    db.session.commit()

    print(search_results)
    return jsonify(search_results)


@app.route('/check_daily_searches', methods=['GET'])
def check_daily_searches():
    shared_user = User.query.first()
    search_count = 0

    if shared_user.last_search_date is not None and shared_user.last_search_date.date() == datetime.utcnow().date():
        search_count = shared_user.daily_search_count

    return jsonify({"search_count": search_count})


@app.route('/product-details', methods=['POST'])
def product_details():
    data = request.json
    asin = data.get('asin')
    item_name = data.get('item_name')  # Get the item name from the request
    amazon_com_price = data.get('amazon_com_price')

    with ThreadPoolExecutor() as executor:
        args = [
            (asin, 'co.uk', True),
            (asin, 'de', True),
            (asin, 'ca', True),
        ]
        futures_to_country_codes = {
            executor.submit(fetch_product_page_with_args, arg): country_code for arg, country_code in zip(args, ['co.uk', 'de', 'ca'])
        }

        product_pages = {}
        for future in as_completed(futures_to_country_codes):
            country_code = futures_to_country_codes[future]
            product_pages[country_code] = future.result()

    # Extract prices using the ASIN
    prices = {
        'Amazon.com': amazon_com_price,
        'Amazon.co.uk': extract_price(product_pages['co.uk'], 'co.uk'),
        'Amazon.de': extract_price(product_pages['de'], 'de'),
        'Amazon.ca': extract_price(product_pages['ca'], 'ca'),
    }
    print("before:", prices)

    # Extract product URLs
    product_urls = {
        'Amazon.com': f'https://www.amazon.com/dp/{asin}',
        'Amazon.co.uk': f'https://www.amazon.co.uk/dp/{asin}',
        'Amazon.de': f'https://www.amazon.de/dp/{asin}',
        'Amazon.ca': f'https://www.amazon.ca/dp/{asin}',
    }

    # If a price is not found using the ASIN, fetch product pages using the item name and extract the price
    with ThreadPoolExecutor() as executor:
        args = [
            (item_name, country_code, False) for country_code in ['co.uk', 'de', 'ca']
            if not prices[f'Amazon.{country_code}']
        ]
        futures_to_country_codes = {
            executor.submit(fetch_product_page_with_args, arg): country_code for arg, country_code in zip(args, ['co.uk', 'de', 'ca'])
        }

        for future in as_completed(futures_to_country_codes):
            country_code = futures_to_country_codes[future]
            product_pages[country_code] = future.result()
            product_urls[f'Amazon.{country_code}'] = f'https://www.amazon.{country_code}/s?k={item_name}'
            prices[f'Amazon.{country_code}'] = extract_price(product_pages[country_code], country_code)

    print("after:", prices)

    return jsonify({'prices': prices, 'urls': product_urls})


@app.route('/save-item-data', methods=['POST'])
def save_item_data():
    data = request.get_json()
    search_data = SearchData(
        query=data['query'],
        time=data['time'],
        item_name=data['item_name'],
        amazon_com_price=data['amazon_com_price'],
        amazon_co_uk_price=data['amazon_co_uk_price'],
        amazon_de_price=data['amazon_de_price'],
        amazon_ca_price=data['amazon_ca_price']
    )
    db.session.add(search_data)
    try:
        db.session.commit()
    except Exception as e:
        print(f"Error while committing the transaction: {e}")
        db.session.rollback()
        return jsonify({'message': 'Error while saving search data.'}), 500

    print("saving:", search_data)
    return jsonify({'message': 'Search data saved successfully.'})


@app.route('/get_past_searches', methods=['GET'])
def get_past_searches():
    all_searches = db.session.query(SearchData).all()
    results = []

    for search in all_searches:
        search_data = {
            'id': search.id,
            'query': search.query,
            'time': search.time,
            'item_name': search.item_name,
            'amazon_com_price': search.amazon_com_price,
            'amazon_co_uk_price': search.amazon_co_uk_price,
            'amazon_de_price': search.amazon_de_price,
            'amazon_ca_price': search.amazon_ca_price
        }
        results.append(search_data)

    return jsonify(results)


# Serve html to the browser
@app.route('/')
def index():
    return render_template("index.html")


@app.route('/past_searches.html')
def past_searches():
    return render_template('past_searches.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)
