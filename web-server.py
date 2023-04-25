import random
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import time
from models import db, SearchData

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///search_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

def fetch_amazon_search_page(query='case', country='ca', is_asin=False):
    headers = get_headers()
    if not is_asin:
        url = f'https://www.amazon.{country}/s?k={query}'
    else:
        url = f'https://www.amazon.{country}/dp/{query}'
    time.sleep(3) # add a 3 second delay
    response = requests.get(url, headers=headers)
    print(response.text)
    return response.text

    # # for testing:
    # with open("html_com_case.txt", 'w') as f:
    #     f.write(response.text)


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36"
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
    soup = BeautifulSoup(page_content, 'html.parser')
    price_element = soup.find('span', {'class': 'a-offscreen'})
    if price_element:
        price = price_element.text.strip()
        price = float(re.sub(r'[^\d.]', '', price))
        if country in ['co.uk', 'de']:
            price = convert_to_usd(price, country)
        return price
    return None


def convert_to_usd(price, country):
    # Implement a conversion function or use an API to get the conversion rate
    # Here's a simple example using fixed conversion rates
    conversion_rates = {
        'co.uk': 1.31,  # GBP to USD
        'de': 1.11,  # EUR to USD
    }
    return price * conversion_rates.get(country, 1)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    text = fetch_amazon_search_page(query)

    # for testing:
    # with open("html_com_laptop.txt", 'r') as f:
    #     text = f.read()

    # Parse the response using BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')

    # Extract the top 10 search results
    search_results = []
    results = soup.find_all('div', {'data-component-type': 's-search-result'})
    # results = soup.find_all('div', {'data-index': lambda x: x and x.isdigit() and int(x) >= 1}, limit=10)
    # results = soup.select(".s-result-item")
    # items = soup.select(".s-result-item")

    # for item in items:
    #     name = soup.select_one("#productTitle")
    #     image = soup.select_one("#landingImage")
    #     price = soup.select_one("#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen, .a-color-price")
    #     rating = soup.select_one("#acrPopover")
    #
    #     if name:
    #         name = name.text.strip()
    #     if image:
    #         image = image["src"]
    #     if price:
    #         price = price.text.strip()
    #     if rating:
    #         rating_text = rating["title"]
    #         rating_value = re.search(r"(\d+(\.\d+)?)", rating_text)
    #         if rating_value:
    #             rating = float(rating_value.group(1))
    #         else:
    #             rating = None
    #
    #     result = {
    #         "name": name,
    #         "image": image,
    #         "price": price,
    #         "rating": rating,
    #         # "asin": asin
    #     }
    #     search_results.append(result)
    #     if len(search_results) >= 10:
    #         break


    for result in results:
        if len(search_results) < 10:
            try:
                # Get the product name
                # name = result.find('span', class_='a-size-medium a-color-base a-text-normal')
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

    print(search_results)
    return jsonify(search_results)


@app.route('/product-details', methods=['POST'])
def product_details():
    data = request.json
    asin = data.get('asin')
    amazon_com_price = data.get('amazon_com_price')

    product_pages = {
        'co.uk': fetch_amazon_search_page(asin, 'co.uk', True),
        'de': fetch_amazon_search_page(asin, 'de', True),
        'ca': fetch_amazon_search_page(asin, 'ca', True),
    }

    # # for testing:
    # with open("html_de_laptop.txt", 'r') as f:
    #     text = f.read()
    #
    # product_pages = {
    #     'co.uk': text,
    #     'de': text,
    #     'ca': text,
    # }

    prices = {
        'Amazon.com': amazon_com_price,
        'Amazon.co.uk': extract_price(product_pages['co.uk'], 'co.uk'),
        'Amazon.de': extract_price(product_pages['de'], 'de'),
        'Amazon.ca': extract_price(product_pages['ca'], 'ca'),
    }

    return jsonify(prices)


@app.route('/save-item-data', methods=['POST'])
def save_search_data():
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
    db.session.commit()
    print("saving:", search_data)
    return jsonify({'message': 'Search data saved successfully.'})


# Serve html to the browser
@app.route('/')
def index():
    return render_template("index.html")


# type this in browser to open: http://localhost:81/
if __name__ == '__main__':
    # fetch_amazon_search_page()
    app.run(host='0.0.0.0', port=81, debug=True)
