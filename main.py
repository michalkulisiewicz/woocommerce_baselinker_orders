from woocommerce import API
import json
import requests
import time
import datetime
import unidecode


url = 'https://api.baselinker.com/connector.php'
token = '1011-10210-OYC7U14WRGM51M3WD5OKJ9TZPSO60MXQ09MJL92BGZ71Z0ME9DERL4INTVCTT3DS'


wcapi = API(
    url="http://alopl.nazwa.pl/wordpress/wpn_alo",
    consumer_key="ck_424cc643b9dc797ea3b66b6c454b89db284fc198",
    consumer_secret="cs_199dcc9c5a59507f0314d892e00cd5d2e5959f1e",
    wp_api=True,
    version="wc/v3"
)

def del_hyphen(post_code):
    post_code = post_code.replace('-','')
    return post_code

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
    #data['shipping_lines'] = shipping_lines_array

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
    billing['email'] = email
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
        payment_method = id['payment_method']

        invoice_fullname = id['invoice_fullname']
        invoice_address = id['invoice_address']
        invoice_city = id['invoice_city']
        invoice_postcode = del_hyphen(id['invoice_postcode'])
        invoice_country = id['invoice_country']
        invoice_company = id['invoice_company']

        email = id['email']
        phone = id['phone']

        delivery_fullname = id['delivery_fullname']
        delivery_address = id['delivery_address']
        delivery_city = id['delivery_city']
        delivery_postcode = del_hyphen(id['delivery_postcode'])
        delivery_country = id['delivery_country']
        delivery_company = id['delivery_company']

        currency = id['currency']

        shipping_total = str(id['delivery_price'])

        order_id = str(id['order_id'])

        line_items_array = []
        shipping_lines_array = []


        for product in id['products']:
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
                                  currency,
                                  shipping_total,
                                  order_id))
    return orders


def chk_available_orders():
    bs_orders = get_orders_bs(source_status)
    if not bs_orders['orders']:
        print('No available orders in status: {} checked at: {}'.format(source_status, datetime.datetime.now()))
        time.sleep(15*60)
        return chk_available_orders()
    else:
        return bs_orders



source_status = input('Provide source status [press enter for default]: ')

if source_status == '':
    source_status = 153957

dest_status = input('Provide destination status: [press enter for default]: ')

if dest_status == '':
    dest_status = 86474


while True:


    bs_orders = chk_available_orders()

    orders = create_woo_order(bs_orders)


    for order in orders:
        resp = wcapi.post("orders", order)
        if resp.status_code == 201:
            resp_json = resp.json()
        elif resp.status_code == 400:
            resp_json = resp.json()
            for id in order['meta_data']:
                if id['key'] == 'baselinker_order_id':
                    order_id = id['value']
                    message = resp_json['message']
                    print('issues with order_id: {}. {}'.format(order_id, message))
        else:
            for id in order['meta_data']:
                if id['key'] == 'baselinker_order_id':
                    order_id = id['value']
                    print('issues with order_id: {}'.format(order_id))

        for id in resp_json['meta_data']:
            if id['key'] == 'baselinker_order_id':
                order_id = id['value']
                change_status = set_order_status(order_id,dest_status)
                if change_status != 200:
                    print('issue with changing status for order_id: {}'.format(order_id))