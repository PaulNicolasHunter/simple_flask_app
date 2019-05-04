from flask import Flask, render_template, request
from user_states.products_stat import Product
from database_handler.sql_conn import SqlManagment

app = Flask(__name__)

sql = SqlManagment()


@app.route('/', methods=['GET'])
def welcome():
	if not check_existing('RECENT'):
		sql.initialize_tables(2)
		records_recent = []
	else:
		records_recent = sql.conn.execute('SELECT * FROM RECENT').fetchall()
	return render_template('homepage.html', products=records_recent)


@app.route('/search_item', methods=['POST'])
def search_product():
	query = request.form['product']

	if not check_existing('PRODUCTS'):
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
		return render_template('available_products.html', products={'found': False, 'data': records_all})


@app.route('/wish_list', methods=['GET'])
def view_wishlist():
	if not check_existing('WISHLIST'):
		sql.initialize_tables(3)
		i_wish_i_had = []
	else:
		i_wish_i_had = sql.conn.execute('SELECT * FROM WISHLIST')
	return render_template('make_a_wish.html', products=i_wish_i_had)


@app.route('/add_wishlist', methods=['POST'])
def add_wish():
	data = request.json
	Product().add_wishlist(data)


def check_existing(q):
	tables = sql.conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
	if (q,) not in tables:
		return False
	else:
		return True


if __name__ == '__main__':
	app.run(debug=True)
