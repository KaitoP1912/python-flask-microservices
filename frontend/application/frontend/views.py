# application/frontend/views.py
import requests
from . import forms
from . import frontend_blueprint
from .. import login_manager
from .api.UserClient import UserClient
from .api.ProductClient import ProductClient
from .api.OrderClient import OrderClient
from flask import render_template, session, redirect, url_for, flash, request

from flask_login import current_user


@login_manager.user_loader
def load_user(user_id):
    return None


@frontend_blueprint.route('/', methods=['GET'])
def home():
    if current_user.is_authenticated:
        session['order'] = OrderClient.get_order_from_session()

    search = request.args.get('q', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    page = request.args.get('page', default=1, type=int)

    try:
        products = ProductClient.get_products(search=search, min_price=min_price, max_price=max_price, page=page, per_page=6)
    except requests.exceptions.ConnectionError:
        products = {
            'results': [],
            'pagination': {
                'page': 1,
                'total_pages': 1
            }
        }

    return render_template('home/index.html', products=products, search=search, min_price=min_price, max_price=max_price)


@frontend_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegistrationForm(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            username = form.username.data

            # Search for existing user
            user = UserClient.does_exist(username)
            if user:
                # Existing user found
                flash('Please try another username', 'error')
                return render_template('register/index.html', form=form)
            else:
                # Attempt to create new user
                user = UserClient.post_user_create(form)
                if user:
                    flash('Thanks for registering, please login', 'success')
                    return redirect(url_for('frontend.login'))

        else:
            flash('Errors found', 'error')

    return render_template('register/index.html', form=form)


@frontend_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('frontend.home'))
    form = forms.LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            api_key = UserClient.post_login(form)
            if api_key:
                session['user_api_key'] = api_key
                user = UserClient.get_user()
                session['user'] = user['result']
                session['role'] = user['result'].get('is_admin', False)

                order = OrderClient.get_order()
                if order.get('result', False):
                    session['order'] = order['result']

                flash('Welcome back, ' + user['result']['username'], 'success')
                return redirect(url_for('frontend.home'))
            else:
                flash('Cannot login', 'error')
        else:
            flash('Errors found', 'error')
    return render_template('login/index.html', form=form)


@frontend_blueprint.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('frontend.home'))


@frontend_blueprint.route('/product/<slug>', methods=['GET', 'POST'])
def product(slug):
    response = ProductClient.get_product(slug)
    item = response['result']

    form = forms.ItemForm(product_id=item['id'])

    if request.method == "POST":
        if 'user' not in session:
            flash('Please login', 'error')
            return redirect(url_for('frontend.login'))
        order = OrderClient.post_add_to_cart(product_id=item['id'], qty=1)
        session['order'] = order['result']
        flash('Order has been updated', 'success')
    return render_template('product/index.html', product=item, form=form)


@frontend_blueprint.route('/checkout', methods=['GET', 'POST'])
def summary():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))
    order = OrderClient.get_order()

    if len(order['result']['items']) == 0:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))

    session['order'] = order['result']

    if request.method == 'POST':
        OrderClient.post_checkout()
        return redirect(url_for('frontend.thank_you'))

    product_map = {}
    cart_total = 0
    for item in order['result']['items']:
        product_id = item['product']
        product_response = ProductClient.get_product_by_id(product_id)
        product = product_response.get('result', {})
        product_map[product_id] = product
        cart_total += int(item['quantity']) * int(product.get('price', 0))

    return render_template('order/index.html', order=order['result'], product_map=product_map, cart_total=cart_total)


@frontend_blueprint.route('/checkout/item/<int:product_id>/increase', methods=['POST'])
def checkout_increase_item(product_id):
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    current_order = OrderClient.get_order().get('result', {'items': []})
    current_qty = 0
    for item in current_order['items']:
        if item['product'] == product_id:
            current_qty = item['quantity']
            break
    OrderClient.post_update_item(product_id, current_qty + 1)
    return redirect(url_for('frontend.summary'))


@frontend_blueprint.route('/checkout/item/<int:product_id>/decrease', methods=['POST'])
def checkout_decrease_item(product_id):
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    current_order = OrderClient.get_order().get('result', {'items': []})
    current_qty = 0
    for item in current_order['items']:
        if item['product'] == product_id:
            current_qty = item['quantity']
            break

    new_qty = max(0, current_qty - 1)
    OrderClient.post_update_item(product_id, new_qty)
    return redirect(url_for('frontend.summary'))


@frontend_blueprint.route('/checkout/item/<int:product_id>/remove', methods=['POST'])
def checkout_remove_item(product_id):
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    OrderClient.post_remove_item(product_id)
    return redirect(url_for('frontend.summary'))


@frontend_blueprint.route('/checkout/clear', methods=['POST'])
def checkout_clear():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    OrderClient.post_clear_order()
    flash('Cart has been cleared', 'info')
    return redirect(url_for('frontend.summary'))


@frontend_blueprint.route('/orders', methods=['GET'])
def orders_history():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    history = OrderClient.get_order_history()
    return render_template('order/history.html', orders=history.get('results', []))


@frontend_blueprint.route('/orders/<int:order_id>', methods=['GET'])
def order_detail(order_id):
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    response = OrderClient.get_order_detail(order_id)
    if 'result' not in response:
        flash('Order not found', 'error')
        return redirect(url_for('frontend.orders_history'))

    order = response['result']
    product_map = {}
    for item in order['items']:
        p_response = ProductClient.get_product_by_id(item['product'])
        product_map[item['product']] = p_response.get('result', {})

    return render_template('order/detail.html', order=order, product_map=product_map)


@frontend_blueprint.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session or not session.get('role', False):
        flash('Permission denied', 'error')
        return redirect(url_for('frontend.home'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip()
        image = request.form.get('image', '').strip()
        price = request.form.get('price', '').strip()

        if name and slug and price:
            ProductClient.post_create_product(name=name, slug=slug, image=image, price=price)
            flash('Product created', 'success')
            return redirect(url_for('frontend.admin'))
        flash('Missing required fields', 'error')

    products = ProductClient.get_products(page=1, per_page=100).get('results', [])
    return render_template('admin/index.html', products=products)


@frontend_blueprint.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if 'user' not in session or not session.get('role', False):
        flash('Permission denied', 'error')
        return redirect(url_for('frontend.home'))

    product_response = ProductClient.get_product_by_id(product_id)
    product = product_response.get('result')
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('frontend.admin'))

    if request.method == 'POST':
        ProductClient.post_update_product(
            product_id=product_id,
            name=request.form.get('name', product['name']),
            slug=request.form.get('slug', product['slug']),
            image=request.form.get('image', product.get('image', '')),
            price=request.form.get('price', product['price'])
        )
        flash('Product updated', 'success')
        return redirect(url_for('frontend.admin'))

    return render_template('admin/edit.html', product=product)


@frontend_blueprint.route('/admin/product/<int:product_id>/delete', methods=['POST'])
def admin_delete_product(product_id):
    if 'user' not in session or not session.get('role', False):
        flash('Permission denied', 'error')
        return redirect(url_for('frontend.home'))

    ProductClient.post_delete_product(product_id)
    flash('Product deleted', 'success')
    return redirect(url_for('frontend.admin'))

@frontend_blueprint.route('/order/thank-you', methods=['GET'])
def thank_you():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))

    session.pop('order', None)
    flash('Thank you for your order', 'success')

    return render_template('order/thankyou.html')