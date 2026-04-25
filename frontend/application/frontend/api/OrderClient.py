# application/frontend/api/OrderClient.py
from flask import session
import requests


class OrderClient:
    @staticmethod
    def _headers():
        return {
            'Authorization': 'Basic ' + session['user_api_key']
        }

    @staticmethod
    def get_order():
        url = 'http://order-service:5003/api/order'
        response = requests.request(method="GET", url=url, headers=OrderClient._headers())
        order = response.json()
        return order

    @staticmethod
    def post_add_to_cart(product_id, qty=1):
        payload = {
            'product_id': product_id,
            'qty': qty
        }
        url = 'http://order-service:5003/api/order/add-item'
        response = requests.request("POST", url=url, data=payload, headers=OrderClient._headers())
        if response:
            order = response.json()
            return order

    @staticmethod
    def post_checkout():
        url = 'http://order-service:5003/api/order/checkout'
        response = requests.request("POST", url=url, headers=OrderClient._headers())
        order = response.json()
        return order

    @staticmethod
    def post_update_item(product_id, qty):
        payload = {
            'product_id': product_id,
            'qty': qty
        }
        response = requests.request("POST", url='http://order-service:5003/api/order/item/update', data=payload, headers=OrderClient._headers())
        return response.json()

    @staticmethod
    def post_remove_item(product_id):
        payload = {
            'product_id': product_id
        }
        response = requests.request("POST", url='http://order-service:5003/api/order/item/remove', data=payload, headers=OrderClient._headers())
        return response.json()

    @staticmethod
    def post_clear_order():
        response = requests.request("POST", url='http://order-service:5003/api/order/clear', headers=OrderClient._headers())
        return response.json()

    @staticmethod
    def get_order_history():
        response = requests.request("GET", url='http://order-service:5003/api/orders/history', headers=OrderClient._headers())
        return response.json()

    @staticmethod
    def get_order_detail(order_id):
        response = requests.request("GET", url='http://order-service:5003/api/order/' + str(order_id), headers=OrderClient._headers())
        return response.json()

    @staticmethod
    def get_order_from_session():
        default_order = {
            'items': {},
            'total': 0,
        }
        return session.get('order', default_order)
