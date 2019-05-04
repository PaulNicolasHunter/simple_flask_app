import sqlite3


class SqlManagment:
	def __init__(self):
		self.conn = sqlite3.connect('products_store.db', check_same_thread=False)

	def initialize_tables(self, cf=None):

		if cf is 1:
			self.conn.execute('''CREATE TABLE PRODUCTS
					 (ID INT PRIMARY KEY     NOT NULL,
					 NAME           TEXT    NOT NULL,
					 PRICE            INT     NOT NULL,
					 IMAGE_URL        CHAR(50),
					 DISCRIPTION         CHAR(250));''')

		elif cf is 2:
			self.conn.execute('''CREATE TABLE RECENT
					 (ID INT PRIMARY KEY     NOT NULL,
					 NAME           TEXT    NOT NULL,
					 PRICE            INT     NOT NULL,
					 IMAGE_URL        CHAR(50),
					 DISCRIPTION         CHAR(250));''')

		elif cf is 3:
			self.conn.execute('''CREATE TABLE WISHLIST
					 (ID INT PRIMARY KEY     NOT NULL,
					 NAME           TEXT    NOT NULL,
					 PRICE            INT     NOT NULL,
					 IMAGE_URL        CHAR(50),
					 DISCRIPTION         CHAR(250));''')

		print("Table created successfully")
