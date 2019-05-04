from flask import Flask, render_template, request
from user_states.products_stat import Product
from database_handler.sql_conn import SqlManagment
from static.some_apis.mail_me import mail_me

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
			if not check_avail(_[0], 'RECENT'):
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
		return render_template('make_a_wish.html', products={"data": i_wish_i_had, "found": False})

	else:
		i_wish_i_had = sql.conn.execute('SELECT * FROM WISHLIST').fetchall()

	return render_template('make_a_wish.html', products={"data": i_wish_i_had, "found": True})


@app.route('/add_wishlist', methods=['POST'])
def add_wishlist():
	id_ = request.form['id']
	dat = sql.conn.execute("SELECT * FROM PRODUCTS where ID = ?", id_).fetchall()[0]
	if not check_avail(id_, 'WISHLIST'):
		Product().add_wishlist(dat)
	sql.conn.commit()
	return ''


@app.route('/remove_it', methods=['POST'])
def remove_it():
	id_ = request.form['id']
	table = request.form['table']
	sql.conn.execute("DELETE from {} where ID = ?;".format(table), id_)
	sql.conn.commit()
	return ''


@app.route('/mail_me', methods=['POST'])
def mail_me_item():
	mail = request.form['mail']
	dat = sql.conn.execute("SELECT * FROM WISHLIST").fetchall()
	message = 'you wishlist \n'
	count = 0
	for _ in dat:
		message += str(count) + ': ' + 'name' + _[1] + '\n' + 'price' + str(_[2]) + '\n' + 'image' + _[
			3] + '\n' + 'discription' + _[4] + '\n\n'
		count += 1
	mail_me(user_mail=mail, pro_mess=message)
	return ''


def check_existing(q):
	tables = sql.conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
	if (q,) not in tables:
		return False
	else:
		return True


def check_avail(id_, tab):
	dat = sql.conn.execute('SELECT ID FROM {} WHERE ID = {}'.format(tab, id_)).fetchall()
	if dat:
		return True
	else:
		return False


if __name__ == '__main__':
	app.run(debug=True)
