from database_handler.sql_conn import SqlManagment


class Product:
	def __init__(self):
		self.all_products = list()
		self.sql = SqlManagment()

	def add_wishlist(self, product):

		if not self.sql.check_existing('WISHLIST'):
			self.sql.initialize_tables(3)
		self.sql.conn.execute(
			'INSERT INTO WISHLIST (ID, NAME, PRICE, IMAGE_URL, DISCRIPTION) VALUES (?, ?, ?, ?, ?)', product)

		self.sql.conn.commit()
		self.sql.conn.close()

	def add_recent(self, product):
		self.sql.conn.execute(
			'INSERT INTO RECENT (ID, NAME, PRICE, IMAGE_URL, DISCRIPTION) VALUES (?, ?, ?, ?, ?)', product)

		self.sql.conn.commit()
		self.sql.conn.close()

	def add_all(self, product):  # we expect the our api gives us response in json format
		self.all_products.append(
			[product['id'], product['name'], product['price'], product['img_url'], product['disc']])

	def update_table(self):
		for _ in self.all_products:
			self.sql.conn.execute(
				'INSERT INTO PRODUCTS (ID, NAME, PRICE, IMAGE_URL, DISCRIPTION) VALUES (?, ?, ?, ?, ?)', _)

		self.sql.conn.commit()
		self.sql.conn.close()

	def add_dummy(self):
		api_data = [{'id': 1, 'name': 'Adidas run', 'price': 4500,
					 'img_url': 'https://images.finishline.com/is/image/FinishLine/B79758_BGW?$Main_gray$',
					 'disc': 'Good for running and hiking shoes'}, {'id': 2, 'name': 'Reebok f1', 'price': 5000,
																	'img_url': 'https://assets.reebok.com/images/h_600,f_auto,q_auto:sensitive,fl_lossy/9bc443cd449e471aa896a8d3008a5cf7_9366/Reebok_Speed_TR_Flexweave__Black_CN5499_01_standard.jpg',
																	'disc': 'best quality in here'},
					{'id': 3, 'name': 'nike sport', 'price': 6050,
					 'img_url': 'https://www.flightclub.com/media/catalog/product/cache/1/image/1600x1140/9df78eab33525d08d6e5fb8d27136e95/8/0/801906_1.jpg',
					 'disc': 'sport edition'}, {'id': 4, 'name': 'bata school', 'price': 4520,
												'img_url': 'https://schoolkart.s3.amazonaws.com/catalog/product/cache/1/small_image/263x390/9df78eab33525d08d6e5fb8d27136e95/S/K/SK-SH-BATA-005_1_14.jpg',
												'disc': 'for your kids, with love'},
					{'id': 5, 'name': 'woodland hard', 'price': 8960,
					 'img_url': 'https://images-na.ssl-images-amazon.com/images/I/71pTqffvbCL._UX395_.jpg',
					 'disc': 'last longer'}, {'id': 6, 'name': 'krassa eleg', 'price': 5400,
											  'img_url': 'https://cdn.shopify.com/s/files/1/1356/3633/files/canvas_category_banner_2_580x.jpg?v=1544600085',
											  'disc': 'elegance in shoes'},
					{'id': 7, 'name': 'Chevit 12', 'price': 3450,
					 'img_url': 'https://rukminim1.flixcart.com/image/332/398/jl6wjgw0/shoe/k/j/f/cb-110-98-6-chevit-navy-blue-original-imaf8dv5zaadhthf.jpeg?q=50',
					 'disc': 'party at feet'},
					{'id': 8, 'name': 'Earton', 'price': 5000,
					 'img_url': 'https://rukminim1.flixcart.com/image/332/398/jg406fk0/shoe/u/t/9/combo-e-787-750-8-earton-multicolor-original-imaf4e2gzzsk2c2j.jpeg?q=50',
					 'disc': 'never worry'}, {'id': 9, 'name': 'Rockfield v2', 'price': 3600,
											  'img_url': 'https://images-eu.ssl-images-amazon.com/images/I/41eDQGIRH7L._SX395_QL70_.jpg',
											  'disc': 'probaby the best ;)'}]
		for _ in api_data:
			self.add_all(_)
