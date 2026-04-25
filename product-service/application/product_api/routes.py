# application/product_api/routes.py
from . import product_api_blueprint
from .. import db
from ..models import Product
from flask import jsonify, request


@product_api_blueprint.route('/api/products', methods=['GET'])
def products():
    query = Product.query

    search = request.args.get('q', '').strip()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    page = max(1, request.args.get('page', default=1, type=int))
    per_page = max(1, min(50, request.args.get('per_page', default=12, type=int)))

    if search:
        pattern = '%' + search + '%'
        query = query.filter((Product.name.like(pattern)) | (Product.slug.like(pattern)))

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    pagination = query.order_by(Product.date_added.desc()).paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for row in pagination.items:
        items.append(row.to_json())

    response = jsonify({
        'results': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': pagination.total,
            'total_pages': pagination.pages
        }
    })
    return response


@product_api_blueprint.route('/api/product/create', methods=['POST'])
def post_create():
    name = request.form['name']
    slug = request.form['slug']
    image = request.form['image']
    price = request.form['price']

    item = Product()
    item.name = name
    item.slug = slug
    item.image = image
    item.price = price

    db.session.add(item)
    db.session.commit()

    response = jsonify({'message': 'Product added', 'product': item.to_json()})
    return response


@product_api_blueprint.route('/api/product/<int:product_id>/update', methods=['POST'])
def update_product(product_id):
    item = Product.query.filter_by(id=product_id).first()
    if item is None:
        return jsonify({'message': 'Cannot find product'}), 404

    name = request.form.get('name', item.name)
    slug = request.form.get('slug', item.slug)
    image = request.form.get('image', item.image)
    price = request.form.get('price', item.price)

    item.name = name
    item.slug = slug
    item.image = image
    item.price = int(price)

    db.session.add(item)
    db.session.commit()
    return jsonify({'message': 'Product updated', 'product': item.to_json()})


@product_api_blueprint.route('/api/product/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    item = Product.query.filter_by(id=product_id).first()
    if item is None:
        return jsonify({'message': 'Cannot find product'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})


@product_api_blueprint.route('/api/product/id/<int:product_id>', methods=['GET'])
def product_by_id(product_id):
    item = Product.query.filter_by(id=product_id).first()
    if item is not None:
        return jsonify({'result': item.to_json()})
    return jsonify({'message': 'Cannot find product'}), 404


@product_api_blueprint.route('/api/product/<slug>', methods=['GET'])
def product(slug):
    item = Product.query.filter_by(slug=slug).first()
    if item is not None:
        response = jsonify({'result': item.to_json()})
    else:
        response = jsonify({'message': 'Cannot find product'}), 404
    return response
