def search_amazon(query, site, asin=None, product_price=False):
    url = build_amazon_search_url(query, site, asin)
    headers = get_request_headers()
    time.sleep(3)  # Add a 3-second delay
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    if asin:
        # If ASIN is provided, only look for the product details in the current page
        items = [soup]
    else:
        items = soup.select(".s-result-item")

    results = []
    for item in items:
        if product_price:
            name = soup.select_one("#productTitle")
            image = soup.select_one("#landingImage")
            price = soup.select_one(
                "#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen, .a-color-price")
            link = url
            rating = soup.select_one("#acrPopover")

            if name:
                name = name.text.strip()
            if image:
                image = image["src"]
            if price:
                price = price.text.strip()
            if rating:
                rating_text = rating["title"]
                rating_value = re.search(r"(\d+(\.\d+)?)", rating_text)
                if rating_value:
                    rating = float(rating_value.group(1))
                else:
                    rating = None
        else:
            asin = item.get("data-asin")
            if not asin:

                continue
            name = item.select_one(
                "h2.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-4, h2.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-2")
            if name:
                name = name.text.strip()
            else:

                continue

            image = item.select_one(".s-image")
            if image:
                image = image["src"]
            else:
                continue

            price = item.select_one(".a-price .a-offscreen")
            if price:
                price = price.text.strip()
            else:
                continue

            link = item.select_one(".a-link-normal.a-text-normal")
            if link:
                link = link["href"]
                if not link.startswith("http"):
                    link = "https://www.amazon.com" + link
            else:
                continue

            rating = item.select_one(
                ".a-icon.a-icon-star-small span.a-icon-alt")
            if rating:
                rating_text = rating.text
                rating_value = re.search(r"(\d+(\.\d+)?)", rating_text)
                if rating_value:
                    rating = float(rating_value.group(1))
                else:
                    rating = None
            else:
                rating = None

        result = {
            "site": site,
            "name": name,
            "image": image,
            "price": price,
            "link": link,
            "rating": rating,
            "asin": asin
        }
        results.append(result)
        if len(results) >= 10:
            break
    return results