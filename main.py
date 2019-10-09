from woocommerce import API
import json
import requests
from requests import Timeout
import time
import datetime
import unidecode


url = 'https://api.baselinker.com/connector.php'
token = '1011-10210-OYC7U14WRGM51M3WD5OKJ9TZPSO60MXQ09MJL92BGZ71Z0ME9DERL4INTVCTT3DS'

wcapi = API(
    url="https://alopl.nazwa.pl/wordpress/wpn_nowypress",
    consumer_key="ck_4314dd53858243c893d4268ccbbd47f33a79b311",
    consumer_secret="cs_033f1c30bc58846be334ebfeae444c302a8dd660",
    wp_api=True,
    version="wc/v3"
)

def del_hyphen(post_code):
    post_code = post_code.replace('-','')
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

    params = {'token': token, 'method': 'getOrders', 'parameters': '{{ "storage_id": 1, "status_id": {} }}'.format(source_status)}

    response = requests.post(url, data=params)

    response = response.text

    orders_bs = json.loads(response)

    return orders_bs

def set_order_status(order_id, status_id):

    order_id = int(order_id)
    status_id = int(status_id)

    params = {'token': token, 'method': 'setOrderStatus',
              'parameters': '{"order_id": %i, "status_id": %i}' % (order_id,status_id)}

    response = requests.post(url, data=params)


    return response.status_code


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

    #check if invoice_fullname is not empty
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
    billing['phone'] = phone

    if delivery_fullname:
        shipping['first_name'] = get_first_name(delivery_fullname)
        shipping['last_name'] = get_second_name(delivery_fullname)
    else:
        shipping['first_name'] = ''
        shipping['last_name'] = ''
        #print('Empty delivery address for order: {}')

    shipping['address_1'] = delivery_address
    shipping['address_2'] = ''
    shipping['city'] = delivery_city
    shipping['state'] = ''
    shipping['postcode'] = delivery_postcode
    shipping['country'] = delivery_country
    shipping['company'] = delivery_company

    #creates special fields in order
    meta_data['key'] = 'baselinker_order_id'
    meta_data['value'] = order_id

    meta_data_array.append(meta_data)

    return data

    # TODO remember about default paramaters: email, sku, quantity, check if they are specified

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

        line_items_array = []
        shipping_lines_array = []
        # meta_data = []
        # meta_data_dict = {}
        # meta_data_dict['key'] = 'bs_order_id'
        # meta_data_dict['value'] =
        # meta_data.append(order_id)


        for product in id['products']:
            shipping_lines_dict = {}
            shipping_lines_dict['method_title'] = id['delivery_method']
            shipping_lines_dict['method_id'] = '2'
            shipping_lines_dict['total'] = str(id['delivery_price'])
            shipping_lines_array.append(shipping_lines_dict)

            line_items_dict = {}

            #line_items_dict['sku'] = product['sku']
            line_items_dict['sku'] = product['sku']
            line_items_dict['quantity'] = product['quantity']
            line_items_dict['price'] = str(product['price_brutto'])
            line_items_array.append(line_items_dict)


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
    return orders


def chk_available_orders():
    bs_orders = get_orders_bs(source_status)
    if not bs_orders['orders']:
        print('No available orders in status: {} checked at: {}'.format(source_status, datetime.datetime.now()))
        time.sleep(30*60)
        return chk_available_orders()
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


source_status = input('Provide source status [press enter for default]: ')

if source_status == '':
    source_status = 153957

dest_status = input('Provide destination status: [press enter for default]: ')

if dest_status == '':
    dest_status = 166337


while True:


    bs_orders = chk_available_orders()

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
                    print('Issue with changing status for order_id: {}'.format(order_id))
                else:
                    print('Changed status of order id: {} to {} at: {}'.format(order_id, dest_status,
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
                        print('Changed status of order id: {} to {} at: {}'.format(order_id, dest_status, datetime.datetime.now() ) )

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

