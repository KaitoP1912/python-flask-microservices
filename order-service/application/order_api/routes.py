# application/order_api/routes.py
from flask import jsonify, request, make_response
from . import order_api_blueprint
from .. import db
from ..models import Order, OrderItem
from .api.UserClient import UserClient


def _to_order_response(order_model):
    data = order_model.to_json()
    data['id'] = order_model.id
    data['status'] = 'open' if order_model.is_open else 'completed'
    return data


def _get_authenticated_user():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return None
    return response['result']


@order_api_blueprint.route('/api/orders', methods=['GET'])
def orders():
    items = []
    for row in Order.query.all():
        items.append(_to_order_response(row))

    response = jsonify(items)
    return response


@order_api_blueprint.route('/api/order/add-item', methods=['POST'])
def order_add_item():
    user = _get_authenticated_user()

    if not user:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    p_id = int(request.form['product_id'])
    qty = int(request.form['qty'])
    u_id = int(user['id'])

    known_order = Order.query.filter_by(user_id=u_id, is_open=1).first()

    if known_order is None:
        known_order = Order()
        known_order.is_open = True
        known_order.user_id = u_id

        order_item = OrderItem(p_id, qty)
        known_order.items.append(order_item)
    else:
        found = False

        for item in known_order.items:
            if item.product_id == p_id:
                found = True
                item.quantity += qty

        if found is False:
            order_item = OrderItem(p_id, qty)
            known_order.items.append(order_item)

    db.session.add(known_order)
    db.session.commit()
    response = jsonify({'result': _to_order_response(known_order)})
    return response


@order_api_blueprint.route('/api/order/item/update', methods=['POST'])
def order_update_item_quantity():
    user = _get_authenticated_user()
    if not user:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    p_id = int(request.form['product_id'])
    qty = max(0, int(request.form['qty']))
    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()
    if open_order is None:
        return make_response(jsonify({'message': 'No order found'}), 404)

    target_item = None
    for item in open_order.items:
        if item.product_id == p_id:
            target_item = item
            break

    if target_item is None:
        return make_response(jsonify({'message': 'Item not found'}), 404)

    if qty == 0:
        db.session.delete(target_item)
    else:
        target_item.quantity = qty

    db.session.add(open_order)
    db.session.commit()
    return jsonify({'result': _to_order_response(open_order)})


@order_api_blueprint.route('/api/order/item/remove', methods=['POST'])
def order_remove_item():
    user = _get_authenticated_user()
    if not user:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    p_id = int(request.form['product_id'])
    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()
    if open_order is None:
        return make_response(jsonify({'message': 'No order found'}), 404)

    for item in open_order.items:
        if item.product_id == p_id:
            db.session.delete(item)
            db.session.add(open_order)
            db.session.commit()
            return jsonify({'result': _to_order_response(open_order)})

    return make_response(jsonify({'message': 'Item not found'}), 404)


@order_api_blueprint.route('/api/order/clear', methods=['POST'])
def order_clear():
    user = _get_authenticated_user()
    if not user:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()
    if open_order is None:
        return make_response(jsonify({'message': 'No order found'}), 404)

    for item in open_order.items:
        db.session.delete(item)

    db.session.add(open_order)
    db.session.commit()
    return jsonify({'result': _to_order_response(open_order)})


@order_api_blueprint.route('/api/order', methods=['GET'])
def order():
    user = _get_authenticated_user()

    if not user:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()

    if open_order is None:
        response = jsonify({'message': 'No order found'})
    else:
        response = jsonify({'result': _to_order_response(open_order)})
    return response


@order_api_blueprint.route('/api/order/checkout', methods=['POST'])
def checkout():
    user = _get_authenticated_user()

    if not user:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    order_model = Order.query.filter_by(user_id=user['id'], is_open=1).first()
    if order_model is None:
        return make_response(jsonify({'message': 'No order found'}), 404)

    order_model.is_open = 0

    db.session.add(order_model)
    db.session.commit()

    response = jsonify({'result': _to_order_response(order_model)})
    return response


@order_api_blueprint.route('/api/orders/history', methods=['GET'])
def orders_history():
    user = _get_authenticated_user()
    if not user:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user_orders = Order.query.filter_by(user_id=user['id']).order_by(Order.date_added.desc()).all()
    data = []
    for row in user_orders:
        data.append(_to_order_response(row))

    return jsonify({'results': data})


@order_api_blueprint.route('/api/order/<int:order_id>', methods=['GET'])
def order_detail(order_id):
    user = _get_authenticated_user()
    if not user:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    item = Order.query.filter_by(id=order_id, user_id=user['id']).first()
    if item is None:
        return make_response(jsonify({'message': 'Order not found'}), 404)

    return jsonify({'result': _to_order_response(item)})
