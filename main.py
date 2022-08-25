from woocommerce import API
import json
import requests
from requests import Timeout
import time
import datetime
import unidecode
import os


def read_config_file():
    path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(path, 'r') as f:
        data = json.load(f)
        return data


def set_up_woo_api(config_file):
    wcapi = API(
        url=config_file['woo_url'],
        consumer_key=config_file['woo_consumer_key'],
        consumer_secret=config_file['woo_consumer_secret'],
        wp_api=True,
        version=config_file['woo_version'],
        timeout=120
    )
    return wcapi


def search_woo_product_by_sku_update_price(sku, bs_price):
    param = {'sku': sku}
    res = wcapi.get("products", params=param).json()
    if len(res) == 1:
        woo_price = res[0]['price']
        if bs_price != woo_price:
            woo_type = res[0]['type']
            woo_parent_id = res[0]['parent_id']
            if woo_type == 'variation':
                woo_variation_id = res[0]['id']
                data = {
                    "regular_price": bs_price
                }
                res = wcapi.put("products/{}/variations/{}".format(woo_parent_id, woo_variation_id), data).json()
                if res['status'] == 400:
                    return False
                else:
                    return True
            else:
                data = {
                    "regular_price": bs_price
                }
                res = wcapi.put("products/{}".format(woo_parent_id), data).json()
                if res['data']['status'] == 400:
                    return False
                else:
                    return True

        else:
            print('bs_price is same as woo_price')
            return True

    else:
        print('Product of sku:{} not found'.format(sku))
        return False


def search_woo_product_by_id(product_id, id, bs_price):
    param = {'product_id': product_id}
    res = wcapi.get("products", params=param).json()
    if len(res) == 1:
        woo_price = res[0]['price']
        if bs_price != woo_price:
            woo_type = res[0]['type']
            woo_parent_id = res[0]['parent_id']
            if woo_type == 'variation':
                woo_variation_id = res[0]['id']
                data = {
                    "regular_price": bs_price
                }
                res = wcapi.put("products/{}/variations/{}".format(woo_parent_id, woo_variation_id), data).json()
                if res['status'] == 400:
                    return False
                else:
                    return True
            else:
                data = {
                    "regular_price": bs_price
                }
                res = wcapi.put("products/{}".format(woo_parent_id), data).json()
                if res['data']['status'] == 400:
                    return False
                else:
                    return True

        else:
            print('bs_price is same as woo_price')
            return True

    else:
        print('Product not found')
        return False


def del_hyphen(post_code):
    post_code = post_code.replace('-', '')
    return post_code


def remove_accent(accented_string):
    unaccented_string = unidecode.unidecode(accented_string)
    return unaccented_string


def get_first_name(fullname):
    first_name = fullname.split(' ')
    return first_name[0]


def get_second_name(fullname):
    second_name = fullname.split(' ')
    return second_name[1]


def get_orders_bs(source_status):
    params = {'token': bs_token, 'method': 'getOrders',
              'parameters': '{{ "storage_id": 1, "status_id": {} }}'.format(source_status)}

    response = requests.post(bs_url, data=params)

    response = response.text

    orders_bs = json.loads(response)

    return orders_bs


def set_order_status(order_id, status_id):
    order_id = int(order_id)
    status_id = int(status_id)

    params = {'token': bs_token, 'method': 'setOrderStatus',
              'parameters': '{"order_id": %i, "status_id": %i}' % (order_id, status_id)}

    response = requests.post(bs_url, data=params)

    return response.status_code


def delete_area_code(phone):
    if '+48' in phone:
        phone = phone.replace('+48', '')
        return phone


def parse_order(
        payment_method,
        invoice_fullname,
        invoice_address,
        invoice_city,
        invoice_postcode,
        invoice_country,
        invoice_company,
        email,
        phone,
        delivery_fullname,
        delivery_address,
        delivery_city,
        delivery_postcode,
        delivery_country,
        delivery_company,
        line_items_array,
        shipping_lines_array,
        currency,
        shipping_total,
        order_id
):
    data = {}
    billing = {}
    shipping = {}
    meta_data = {}

    meta_data_array = []

    data['billing'] = billing
    data['shipping'] = shipping
    data['line_items'] = line_items_array
    data['meta_data'] = meta_data_array
    data['shipping_lines'] = shipping_lines_array

    data['payment_method'] = payment_method
    data['payment_method_title'] = payment_method
    data['currency'] = currency
    data['shipping_total'] = shipping_total

    data['status'] = 'processing'
    data['set_paid'] = True

    # check if invoice_fullname is not empty
    if invoice_fullname:
        billing['first_name'] = get_first_name(invoice_fullname)
        billing['last_name'] = get_second_name(invoice_fullname)
    else:
        billing['first_name'] = ''
        billing['last_name'] = ''

    billing['address_1'] = invoice_address
    billing['address_2'] = ''
    billing['city'] = invoice_city
    billing['state'] = ''
    billing['postcode'] = invoice_postcode
    billing['country'] = invoice_country
    billing['company'] = invoice_company
    billing['email'] = 'alopolskaali@gmail.com'
    phone = delete_area_code(phone)
    billing['phone'] = phone

    if delivery_fullname:
        shipping['first_name'] = get_first_name(delivery_fullname)
        shipping['last_name'] = get_second_name(delivery_fullname)
    else:
        shipping['first_name'] = ''
        shipping['last_name'] = ''

    shipping['address_1'] = delivery_address
    shipping['address_2'] = ''
    shipping['city'] = delivery_city
    shipping['state'] = ''
    shipping['postcode'] = delivery_postcode
    shipping['country'] = delivery_country
    shipping['company'] = delivery_company

    # creates special fields in order
    meta_data['key'] = 'baselinker_order_id'
    meta_data['value'] = order_id

    meta_data_array.append(meta_data)

    return data


def create_woo_order(bs_orders):
    orders = []

    for id in bs_orders['orders']:
        payment_method = remove_accent(id['payment_method'])

        invoice_fullname = remove_accent(id['invoice_fullname'])
        invoice_address = remove_accent(id['invoice_address'])
        invoice_city = remove_accent(id['invoice_city'])
        invoice_postcode = del_hyphen(id['invoice_postcode'])
        invoice_country = remove_accent(id['invoice_country'])
        invoice_company = remove_accent(id['invoice_company'])

        email = remove_accent(id['email'])
        phone = id['phone']

        delivery_fullname = remove_accent(id['delivery_fullname'])
        delivery_address = remove_accent(id['delivery_address'])
        delivery_city = remove_accent(id['delivery_city'])
        delivery_postcode = del_hyphen(id['delivery_postcode'])
        delivery_country = remove_accent(id['delivery_country'])
        delivery_company = remove_accent(id['delivery_company'])

        currency = id['currency']

        shipping_total = str(id['delivery_price'])

        order_id = str(id['order_id'])

        shipping_lines_array = []

        shipping_lines_dict = {}
        shipping_lines_dict['method_title'] = id['delivery_method']
        shipping_lines_dict['method_id'] = '2'
        shipping_lines_dict['total'] = str(id['delivery_price'])
        shipping_lines_array.append(shipping_lines_dict)

        line_items_array = create_products_list(id, order_id)
        if line_items_array:
            orders.append(parse_order(payment_method,
                                      invoice_fullname,
                                      invoice_address,
                                      invoice_city,
                                      invoice_postcode,
                                      invoice_country,
                                      invoice_company,
                                      email,
                                      phone,
                                      delivery_fullname,
                                      delivery_address,
                                      delivery_city,
                                      delivery_postcode,
                                      delivery_country,
                                      delivery_company,
                                      line_items_array,
                                      shipping_lines_array,
                                      currency,
                                      shipping_total,
                                      order_id))
        else:
            change_status = set_order_status(order_id, '86800')
            if change_status != 200:
                print('Issue with changing status for order_id: {}'.format(order_id))
            else:
                print('Changed failed order status order id: {} to {} at: {}'.format(order_id, dest_status,
                                                                                     datetime.datetime.now()))
        return orders


def create_products_list(id, order_id):
    line_items_array = []

    for product in id['products']:
        line_items_dict = {}
        bs_price = str(product['price_brutto'])
        sku = product['sku']
        line_items_dict['sku'] = sku
        line_items_dict['quantity'] = product['quantity']
        line_items_dict['price'] = bs_price

        correct_price = search_woo_product_by_sku_update_price(sku, bs_price)
        if correct_price == True:
            line_items_array.append(line_items_dict)
        else:
            print('Issue with order_id:{} with sku:{}'.format(order_id, sku))
            return None

    return line_items_array


def check_available_orders():
    try:
        bs_orders = get_orders_bs(source_status)
    except:
        time.sleep(30 * 60)
        bs_orders = get_orders_bs(source_status)

    if not bs_orders['orders']:
        print('No available orders in status: {} checked at: {}'.format(source_status, datetime.datetime.now()))
        time.sleep(30 * 60)
        return check_available_orders()
    else:
        return bs_orders


def get_bs_order_id(order):
    meta_data_list = order['meta_data']
    for item in meta_data_list:
        if item['key'] == 'baselinker_order_id':
            order_id = item['value']
            return order_id


def check_if_order_exist(new_order_id):
    orders = wcapi.get("orders").json()
    for order in orders:
        existing_order_id = get_bs_order_id(order)
        if new_order_id == existing_order_id:
            return True
        else:
            return False


def run():
    config_file = read_config_file()
    global bs_url, bs_token, wcapi, source_status, dest_status
    bs_url = config_file['bs_api_endpoint']
    bs_token = config_file['bs_token']
    wcapi = set_up_woo_api(config_file)
    source_status = config_file['bs_source_status']
    dest_status = config_file['woo_destination_status']

    while True:
        bs_orders = check_available_orders()

        orders = create_woo_order(bs_orders)

        for order in orders:
            try:
                resp = wcapi.post("orders", order)
            except Timeout as err:
                print('Request timed out at: {} with error: {}'.format(datetime.datetime.now(), err))
                new_order_id = get_bs_order_id(order)
                order_exist = check_if_order_exist(new_order_id)
                if order_exist == True:
                    print('Order {} timeout but was sucessfully added'.format(new_order_id))
                    change_status = set_order_status(new_order_id, dest_status)
                    if change_status != 200:
                        print('Issue with changing status for order_id: {}'.format(new_order_id))
                    else:
                        print('Changed status of order id: {} to {} at: {}'.format(new_order_id, dest_status,
                                                                                   datetime.datetime.now()))

            if resp.status_code == 201:
                resp_json = resp.json()

                for id in resp_json['meta_data']:
                    if id['key'] == 'baselinker_order_id':
                        order_id = id['value']
                        change_status = set_order_status(order_id, dest_status)
                        if change_status != 200:
                            print('Issue with changing status for order_id: {}'.format(order_id))
                        else:
                            print('Changed status of order id: {} to {} at: {}'.format(order_id, dest_status,
                                                                                       datetime.datetime.now()))

            elif resp.status_code == 400:
                resp_json = resp.json()
                for id in order['meta_data']:
                    if id['key'] == 'baselinker_order_id':
                        order_id = id['value']
                        message = resp_json['message']
                        print('Issues with order_id: {}. {}'.format(order_id, message))
            else:
                for id in order['meta_data']:
                    if id['key'] == 'baselinker_order_id':
                        order_id = id['value']
                        print('Issues with order_id: {}'.format(order_id))


run()
