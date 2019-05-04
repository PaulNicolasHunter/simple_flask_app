# A product(viewing, searching and wishlisting) store using flask.
A simple flask application for product viewing, searching and wish-list creation

## some pre-requists
- sqlite3
- Flask

## making the mailing service funtionable
- edit the sender (mail and password) and receiver mail in /static/some_api/mail_me.py

## Add more dummy data at user_states/product_stat.py (in add dummy function). It is exected that the function receives data from some sort of api in JSON format, but in our case we manually write the JSON data, where - 
- ID is the key of the product 
- NAME is the name of the product 
- PRICE is the price of the product 
- IMAGE_URL is the image url of the product 
- DISCRIPTION is the discription of the product 

## run app.py
