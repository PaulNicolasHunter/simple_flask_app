import logging
import re
import time
import bottlenose
import firebase_admin
import xmltodict as xmltodict
from bs4 import BeautifulSoup

# Response Group
RESPONSE_GROUP = 'AlternateVersions, EditorialReview, Images, ItemAttributes, PromotionSummary, OfferFull'
SEARCH_INDEX = 'Books'
BROWSE_NODE = '976390031'
KEYWORD = ''

amazon = bottlenose.Amazon(AWSAccessKeyId='',
                           AWSSecretAccessKey='', AssociateTag='utsavmang',
                           Region='IN',
                           Parser=lambda text: BeautifulSoup(text, 'xml').decode_contents()
                           )

logging.getLogger().setLevel(logging.INFO)


def get_updatable_data(product_id, product_data, merchant_id):
    """
    Used to create python dictionary that can be passed to Firebase's Updated
    function such that updating do not result in overwritting unique data attributes
    for each merchant (Flipkart, Amazon.. etc) such as - prices, delivery details,
    merchant detail page urls etc.
    For example: .../{product_id}/prices/{merchant_id}/mrp/
    :param product_id: Id of the product
    :param product_data: Data of product
    :param merchant_id: Unique 4 digit ID of merchant for example 'fpkt' of Flipkart
    :return: Dictionary that can be passed to Firebase's Update Function
    For example:
    {
        "{product_id}/{non_unique_key_N}": {...},
        "{product_id}/{non_unique_key_N+1}": {...},
        "{product_id}/{unique_key_N}/{merchant_id}": {...},
        "{product_id}/{unique_key_N+1}/{merchant_id}": {...},
        ... : {...}
    }
    """

    # Keys that are unique to every merchant
    unique_keys_for_merchants = ['price/' + merchant_id,
                                 'delivery/' + merchant_id,
                                 'merchant_detail_page/' + merchant_id]

    updatedable_data = {}

    for product_attr_key in product_data:
        if product_attr_key in unique_keys_for_merchants:
            # Unique key
            updatedable_data[product_id + '/' + product_attr_key] = product_data[product_attr_key]

        # Non-unique key
        updatedable_data[product_id + '/' + product_attr_key] = product_data[product_attr_key]

    return updatedable_data


def amazon_search_api(data, context):
    _start = time.perf_counter()
    print(data)
    print(context)

    query_data = data.get('delta')
    query_id = query_data.get('id')  # ID of search query
    logging.info('SEARCH_QUERY_ID: ' + str(query_id))
    query = query_data.get('query')  # Search Query

    if query is None:
        logging.warning('NO_SEARCH_QUERY_FOUND')
        return None

    start = time.perf_counter()
    amazon_request = AmazonRequest(bottlenose_amazon=amazon)
    response = amazon_request.request_item_search(query, SEARCH_INDEX, BROWSE_NODE, RESPONSE_GROUP, '1')
    print(response)
    print('AmazonRequest(): %s' % (time.perf_counter() - start))

    # Parse search results from response
    # And organise in predefined DOM
    start = time.perf_counter()
    products = response.get_product_data_from_response()  # Response in XML
    print('get_product_data_from_response(): %s' % (time.perf_counter() - start))
    results = {}
    logging.info('%s search results found' % len(products))

    start = time.perf_counter()
    for product in products:
        # formatted_product is Py Dict w/ correct Product ID
        formatted_product = AmazonProductBooks(product).get_format_product_data()

        # Convert response to pre-defined database schema
        product_id = list(formatted_product.keys())[0]
        formatted_product = BookMapping(product_id, formatted_product[product_id]).mapping_for_amzn_first_time()

        # Update results
        results = {**{product_id: formatted_product}, **results}
    print('Raw JSON -> Formatted JSON: %s' % (time.perf_counter() - start))

    start = time.perf_counter()
    # create python dictionary that can be passed to Firebase's Updated
    # function such that updating do not result in overwriting unique data attributes
    # such as "price/amzn" and "merchant_detail_page/amzn"
    updatable_results = {}
    for result_id in results:
        updatable_result = get_updatable_data(result_id, results[result_id], 'amzn')
        updatable_results = {**updatable_result, **updatable_results}
    print('Updateable results: %s' % (time.perf_counter() - start))

    # Add results to Firebase Realtime Database
    start = time.perf_counter()
    db.reference('search/results').child(query_id).update(updatable_results)
    print('End: %s' % (time.perf_counter() - start))

    print('Program Execution {0}'.format((time.perf_counter() - _start)))


class AmazonRequest(object):

    def _init_(self, bottlenose_amazon):
        # TODO Check if isinstance(bottlenose_amazon, bottlenose.Amazon)
        self.amazon = bottlenose_amazon

    def request_item_search(self, keywords, search_index, browse_node, response_group, item_page='', min_price='',
                            max_price=''):
        """
            :param max_price: Specifies the maximum item price in the response. Prices are returned in the lowest currency
                                denomination. For example, 3241 is $32.41.
            :param min_price: Specifies the minimum item price in the response. Prices are returned in the lowest currency
                                denomination. For example, 3241 is $32.41.
            :return:
        """

        return AmazonResponse(
            self.amazon.ItemSearch(Keywords=keywords, SearchIndex=search_index, BrowseNode=browse_node,
                                   ResponseGroup=response_group, ItemPage=item_page,
                                   MaximumPrice=max_price,
                                   MinimumPrice=min_price), self)

    def request_item_lookup(self, item_id, response_group):
        """
        Look up a specific ASIN
        """
        return AmazonResponse(self.amazon.ItemLookup(ItemId=item_id, ResponseGroup=response_group), self)


class AmazonResponse(object):

    def _init_(self, response, request):
        self.response = response
        self.request = request

        start = time.perf_counter()
        self.response_dict = self.xml_to_dict_amzn()
        print('xml to dict: ' + str(time.perf_counter() - start))

        self.response_status = self.get_response_status()
        if self.response_status['is_valid'] is False:
            logging.error(str(self.response_status['message']))

    def xml_to_dict_amzn(self):
        return xmltodict.parse(self.response, attr_prefix='__', cdata_key='_text')

    def get_response_status(self):

        response_status = {
            'is_valid': False,
            'message': ''
        }

        # next(iter(self.response)) is either ItemLookupResponse or ItemSearchResponse etc

        is_valid = self.response_dict[next(iter(self.response_dict))]['Items']['Request']['IsValid']

        if is_valid == 'True' and 'Errors' not in self.response_dict[next(iter(self.response_dict))]['Items'][
            'Request']:
            response_status['is_valid'] = True
            return response_status
        elif is_valid == 'False' or 'Errors' in self.response_dict[next(iter(self.response_dict))]['Items']['Request']:
            response_status['is_valid'] = False
            response_status['message'] = self.response_dict[next(iter(self.response_dict))]['Items']['Request'][
                'Errors']
            logging.warning('Response Error - ' + str(response_status['message']))
            return response_status
        else:
            logging.warning('Could not detect if response is valid or not' + str(self.response_dict))
            response_status['is_valid'] = False
            response_status['message'] = 'Could not detect if response is valid or not' + str(self.response_dict)
            return response_status

    def get_product_data_from_response(self):
        start_a = time.perf_counter()
        """
        :return: A list of products in response if there is no error in response else return None
        """
        if self.response_status['is_valid']:
            # When single product in the data is in dict otherwise list
            product_detail = self.response_dict.get(next(iter(self.response_dict))).get('Items').get('Item')
            print('IN_FUNCTION: get_product_data_from_response(): ' + str(time.perf_counter() - start_a))
            return product_detail if isinstance(product_detail, list) else [product_detail]
        else:
            return []


class AmazonProductBooks(object):

    def _init_(self, product_detail):
        self.product_detail = product_detail

        self.product_id = product_detail.get('ASIN')

        self.has_isbn_object = self.has_isbn_or_eisbn()  # Temporary variable to hold value returned by has_isbn_or_eisbn(self)

        self.product_id = self.has_isbn_object[1]
        if self.has_isbn_object[0] and len(self.product_id) == 10:
            corrected_isbn = convert_10_to_13(self.product_id)
            self.product_id = corrected_isbn
            self.product_detail['ItemAttributes'][
                self.has_isbn_object[2]] = corrected_isbn  # Correct ISBN/EISBN in product detail

    def get_format_product_data(self):
        product_details = {self.product_id: self.product_detail}

        return product_details

    def has_isbn_or_eisbn(self):
        if 'ISBN' in self.product_detail['ItemAttributes']:
            return True, self.product_detail['ItemAttributes']['ISBN'], 'ISBN'

        elif 'EISBN' in self.product_detail['ItemAttributes']:
            return True, self.product_detail['ItemAttributes']['EISBN'], 'EISBN'

        else:
            logging.info('Product ID {} does not contain either ISBN or EISBN.'.format(self.product_id))
            return False, self.product_detail['ASIN'], 'ASIN'

    def get_alternate_versions_id(self):
        alt_prod_ids = []

        if isinstance(self.product_detail.get('AlternateVersions', {}).get('AlternateVersion', {}), list):
            # Multiple Alternative Version fields
            for alt_prod in self.product_detail.get('AlternateVersions', {}).get('AlternateVersion', {}):
                if alt_prod.get('ASIN', None) is not None:
                    alt_prod_ids.append(alt_prod.get('ASIN'))
        elif isinstance(self.product_detail.get('AlternateVersions', {}).get('AlternateVersion', {}), dict):
            # Single Alternative Version field
            if self.product_detail.get('AlternateVersions', {}).get('AlternateVersion', {}).get('ASIN',
                                                                                                None) is not None:
                alt_prod_ids.append(
                    self.product_detail.get('AlternateVersions', {}).get('AlternateVersion', {}).get('ASIN'))

        return alt_prod_ids


def check_digit_13(isbn):
    assert len(isbn) == 12
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        if i % 2:
            w = 3
        else:
            w = 1
        sum += w * c
    r = 10 - (sum % 10)
    if r == 10:
        return '0'
    else:
        return str(r)


def convert_10_to_13(isbn):
    assert len(isbn) == 10
    prefix = '978' + isbn[:-1]
    check = check_digit_13(prefix)
    return prefix + check


class BookMapping(object):

    def _init_(self, product_id, product_detail):
        self.product_detail = product_detail
        self.product_id = product_id

    def mapping_for_amzn_first_time(self):
        """
        Convert Raw Product Data in Py Dict to JSON as per Final/Normalised Books DB
        -----------------------------------------------------------------------------
        Helps in extracting information from Py Dict of Books Product self.product_data which is
        in Raw form as fetched from FASO (Flipkart, Amazon, Snapdeal and Others)'s APIs
        into self.product_data structure that is saved in Final aka Normalised self.product_database for Books
        """

        amazon_product_detail = {

            'id': self.product_id,

            'price/amzn': {

                'selling_price': {
                    'currency': self.product_detail.get('Offers', {}).get('Offer', {}).get('OfferListing', {}).get(
                        'Price', {}).get(
                        'CurrencyCode', None),
                    'amount': get_sp(self.product_detail),
                    'formatted_price': get_formatted_sp(self.product_detail)
                },

                'mrp': {
                    'currency': self.product_detail.get('ItemAttributes', {}).get('ListPrice', {}).get('CurrencyCode',
                                                                                                       None),
                    'amount': get_mrp(self.product_detail),
                    'formatted_price': get_formatted_mrp(self.product_detail)
                }

            },
            'merchant_detail_page/amzn': {
                'name': 'Amazon India',
                'url': self.product_detail.get('DetailPageURL', None),
                'icon_url': 'https://firebasestorage.googleapis.com/v0/b/pagenumber21-147f8.appspot.com/o/merchant_icon%2Famazon_india_100.jpg?alt=media&token=38152006-4b59-4a29-8499-b10e3fd66c72'
            },

            'name': self.product_detail.get('ItemAttributes', {}).get('Title', None),

            'product_description': get_description(self.product_detail),

            'page_count': self.product_detail.get('ItemAttributes', {}).get('NumberOfPages', None),

            'publisher': self.product_detail.get('ItemAttributes', {}).get('Publisher', None),

            'published_on': self.product_detail.get('ItemAttributes', {}).get('PublicationDate', None),

            'binding': self.product_detail.get('ItemAttributes', {}).get('Binding', None),

            'ISBN': self.product_detail.get('ItemAttributes', {}).get('ISBN',
                                                                      self.product_detail.get('ItemAttributes', {}).get(
                                                                          'EISBN', None)),

            'image_sets': [{
                'large_image': {
                    'height': {
                        'units': self.product_detail.get('LargeImage', {}).get('Height', {}).get('__Units', None),
                        'value': self.product_detail.get('LargeImage', {}).get('Height', {}).get('_text', None)
                    },
                    'width': {
                        'units': self.product_detail.get('LargeImage', {}).get('Width', {}).get('__Units', None),
                        'value': self.product_detail.get('LargeImage', {}).get('Width', {}).get('_text', None)
                    },
                    'url': self.product_detail.get('LargeImage', {}).get('URL', {})
                },
                'medium_image': {
                    'height': {
                        'units': self.product_detail.get('MediumImage', {}).get('Height', {}).get('__Units', None),
                        'value': self.product_detail.get('MediumImage', {}).get('Height', {}).get('_text', None)
                    },
                    'width': {
                        'units': self.product_detail.get('MediumImage', {}).get('Width', {}).get('__Units', None),
                        'value': self.product_detail.get('MediumImage', {}).get('Width', {}).get('_text', None)
                    },
                    'url': self.product_detail.get('MediumImage', {}).get('URL', None)
                },
                'small_image': {
                    'height': {
                        'units': self.product_detail.get('SmallImage', {}).get('Height', {}).get('__Units', None),
                        'value': self.product_detail.get('SmallImage', {}).get('Height', {}).get('_text', None)
                    },
                    'width': {
                        'units': self.product_detail.get('SmallImage', {}).get('Width', {}).get('__Units', None),
                        'value': self.product_detail.get('SmallImage', {}).get('Width', {}).get('_text', None)
                    },
                    'url': self.product_detail.get('SmallImage', {}).get('URL', None)
                }
            }]
        }

        # Author
        if type(self.product_detail.get('ItemAttributes', {}).get('Author', None)) is str:
            amazon_product_detail['authors'] = [
                {'author_name': self.product_detail.get('ItemAttributes', {}).get('Author', None)}]
        elif type(self.product_detail.get('ItemAttributes', {}).get('Author', None)) is list:
            amazon_product_detail['authors'] = []
            for author_name in self.product_detail.get('ItemAttributes', {}).get('Author', {}):
                amazon_product_detail['authors'].append(
                    {
                        'author_name': author_name
                    }
                )

        if type(self.product_detail.get('ItemAttributes', {}).get('Languages', {}).get('Language', [{}])) is type(list):
            amazon_product_detail['language'] = \
                self.product_detail.get('ItemAttributes', {}).get('Languages', {}).get('Language', [{}])[
                    0].get('Name', None)
        elif type(self.product_detail.get('ItemAttributes', {}).get('Languages', {}).get('Language', [{}])) is type(
                list):
            amazon_product_detail['language'] = self.product_detail.get('ItemAttributes', {}).get('Languages', {}).get(
                'Language',
                [{}]).get('Name',
                          None)

        return amazon_product_detail


def clean_html(raw_html):
    clean_r = re.compile('<.*?>')
    clean_text = re.sub(clean_r, '', raw_html)
    return clean_text


def get_mrp(product_detail):
    mrp_amount = product_detail.get('ItemAttributes', {}).get('ListPrice', {}).get('Amount', None)
    mrp_amount = mrp_amount if mrp_amount is None or len(mrp_amount) < 2 else float(
        mrp_amount[:-2] + '.' + mrp_amount[-2:])

    return mrp_amount


def get_sp(product_detail):
    sp_amount = product_detail.get('Offers', {}).get('Offer', {}).get('OfferListing', {}).get('Price', {}).get(
        'Amount', None)
    sp_amount = sp_amount if sp_amount is None or len(sp_amount) < 2 else float(
        sp_amount[:-2] + '.' + sp_amount[-2:])

    return sp_amount


def get_description(product_detail):
    # Description - Remove HTML tags
    product_description = product_detail.get('EditorialReviews', {}).get('EditorialReview', {}).get('Content',
                                                                                                    None)
    product_description = clean_html(
        product_description) if product_description is not None else product_description

    return product_description


def get_formatted_sp(product_detail):
    sp_currency_code = product_detail.get('Offers', {}).get('Offer', {}).get('OfferListing', {}).get('Price', {}).get(
        'CurrencyCode', None)
    if sp_currency_code == 'INR':
        sp_currency_code = '₹'

    sp_amount = get_sp(product_detail)

    if sp_amount is None or sp_currency_code is None:
        return None

    return sp_currency_code + ' ' + str(sp_amount)


def get_formatted_mrp(product_detail):
    mrp_currency_code = product_detail.get('ItemAttributes', {}).get('ListPrice', {}).get('CurrencyCode', None)
    if mrp_currency_code == 'INR':
        mrp_currency_code = '₹'

    mrp_amount = get_mrp(product_detail)

    if mrp_amount is None or mrp_currency_code is None:
        return None

    return mrp_currency_code + ' ' + str(mrp_amount)