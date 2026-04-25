# application/frontend/api/ProductClient.py
import requests


class ProductClient:

    @staticmethod
    def get_products(search=None, min_price=None, max_price=None, page=1, per_page=12):
        params = {
            'page': page,
            'per_page': per_page
        }
        if search:
            params['q'] = search
        if min_price not in (None, ''):
            params['min_price'] = min_price
        if max_price not in (None, ''):
            params['max_price'] = max_price

        r = requests.get('http://product-service:5002/api/products', params=params)
        products = r.json()
        return products

    @staticmethod
    def get_product(slug):
        response = requests.request(method="GET", url='http://product-service:5002/api/product/' + slug)
        product = response.json()
        return product

    @staticmethod
    def get_product_by_id(product_id):
        response = requests.request(method="GET", url='http://product-service:5002/api/product/id/' + str(product_id))
        return response.json()

    @staticmethod
    def post_create_product(name, slug, image, price):
        payload = {
            'name': name,
            'slug': slug,
            'image': image,
            'price': price
        }
        response = requests.request(method="POST", url='http://product-service:5002/api/product/create', data=payload)
        return response.json()

    @staticmethod
    def post_update_product(product_id, name, slug, image, price):
        payload = {
            'name': name,
            'slug': slug,
            'image': image,
            'price': price
        }
        response = requests.request(method="POST", url='http://product-service:5002/api/product/' + str(product_id) + '/update', data=payload)
        return response.json()

    @staticmethod
    def post_delete_product(product_id):
        response = requests.request(method="POST", url='http://product-service:5002/api/product/' + str(product_id) + '/delete')
        return response.json()
