from flask import Flask, render_template, request
from user_states.products_stat import Product
from database_handler.sql_conn import SqlManagment

app = Flask(__name__)

sql = SqlManagment()


@app.route('/', methods=['GET'])
def welcome():
	if ('RECENT',) not in sql.conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall():
		print(sql.conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall())
		sql.initialize_tables(2)
		records_recent = []
	else:
		records_recent = sql.conn.execute('SELECT * FROM RECENT').fetchall()

	return render_template('homepage.html', products=records_recent)


@app.route('/search_item', methods=['POST'])
def search_product():
	query = request.form['product']
	print(query)
	if ('PRODUCTS',) not in sql.conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall():
		sql.initialize_tables(1)
		update_products = Product()
		update_products.add_dummy()
		update_products.update_table()

	records_all = sql.conn.execute(f"SELECT * FROM PRODUCTS WHERE (NAME LIKE '%{query}%')").fetchall()

	if records_all:
		for _ in records_all:
			Product().add_recent(_)
		return render_template('available_products.html', products={'found': True, 'data': records_all})
	else:
		records_all = sql.conn.execute("SELECT * FROM PRODUCTS").fetchall()
		print(records_all)
		return render_template('available_products.html', products={'found': False, 'data': records_all})


@app.route('/add_wishlist', methods=['POST'])
def add_wish():
	data = request.json
	print(data)


@app.route('/wish_list', methods=['GET'])
def view_wishlist():
	i_wish_i_had = sql.conn.execute('SELECT * FROM WISHLIST')
	return render_template('make_a_wish_.html', products=i_wish_i_had)


if __name__ == '__main__':
	app.run(debug=True)
