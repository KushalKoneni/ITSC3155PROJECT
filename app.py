#!/usr/bin/env python3

from authentication.authTools import login_pipeline, update_passwords, hash_password
from database.db import Database
from flask import Flask, render_template, request, flash, redirect
from core.session import Sessions
import sqlite3

app = Flask(__name__)
HOST, PORT = 'localhost', 8080
global username, products, db, sessions
username = 'default'
db = Database('database/storeRecords.db')
products = db.get_full_inventory()
sessions = Sessions()
sessions.add_new_session(username, db)

@app.route('/')
def index_page():
    """
    Renders the index page when the user is at the `/` endpoint, passing along default flask variables.

    args:
        - None

    returns:
        - None
    """
    return render_template('index.html', username=username, products=products, sessions=sessions)


@app.route('/login')
def login_page():
    """
    Renders the login page when the user is at the `/login` endpoint.

    args:
        - None

    returns:
        - None
    """
    return render_template('login.html')


@app.route('/home', methods=['POST'])
def login():
    """
    Renders the home page when the user is at the `/home` endpoint with a POST request.

    args:
        - None

    returns:
        - None

    modifies:
        - sessions: adds a new session to the sessions object

    """
    username = request.form['username']
    password = request.form['password']
    if login_pipeline(username, password):
        sessions.add_new_session(username, db)
        return render_template('home.html', products=products, sessions=sessions)
    else:
        print(f"Incorrect username ({username}) or password ({password}).")
        return render_template('index.html')


@app.route('/register')
def register_page():
    """
    Renders the register page when the user is at the `/register` endpoint.

    args:
        - None

    returns:
        - None
    """
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register():
    """
    Renders the index page when the user is at the `/register` endpoint with a POST request.

    args:
        - None

    returns:
        - None

    modifies:
        - passwords.txt: adds a new username and password combination to the file
        - database/storeRecords.db: adds a new user to the database
    """
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    salt, key = hash_password(password)
    update_passwords(username, key, salt)
    db.insert_user(username, key, email, first_name, last_name)
    return render_template('index.html')

@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Renders the checkout page when the user is at the `/checkout` endpoint with a POST request.

    args:
        - None

    returns:
        - None

    modifies:
        - sessions: adds items to the user's cart
    """
    order = {}
    user_session = sessions.get_session(username)
    for item in products:
        print(f"item ID: {item['id']}")
        if request.form[str(item['id'])] > '0':
            count = request.form[str(item['id'])]
            order[item['item_name']] = count
            user_session.add_new_item(
                item['id'], item['item_name'], item['price'], count)

    user_session.submit_cart()

    return render_template('checkout.html', order=order, sessions=sessions, total_cost=user_session.total_cost)

@app.route('/book-flights')
def book_flights():
    return render_template('book-flights.html')

"""
Renders the booking form for a GET request to the root URL and displays flights matching the origin and destination cities for a POST request.

Args:
    None

Returns:
    If a POST request is made, returns a rendered template named 'flights.html' displaying the matching flights.
    If a GET request is made, returns a rendered  template named 'book_flight.html' displaying the booking form.

Modifies:
    None, but retrieves data from a SQLite database and a form.
"""

@app.route('/', methods=['GET', 'POST'])
def book_flight():
    if request.method == 'POST':
        # Retrieve the selected origin and destination cities from the form
        origin_city = request.form['city_1']
        destination_city = request.form['city_2']

        # Connect to the database and query the flights table for flights that match the selected cities
        conn = sqlite3.connect('database/storeRecords.db')
        
        c = conn.cursor()
        c.execute("SELECT * FROM flights WHERE origin=? AND destination=?", (origin_city, destination_city))
        flights = c.fetchall()

        # Pass the flights to the template and render it
        return render_template('flights.html', flights=flights)

    # Render the booking form
    return render_template('book_flight.html')
"""
Renders the cart page for both GET and POST requests to the '/cart' endpoint.

Args:
    None

Returns:
    If a POST request is made, returns a rendered template named 'cart.html' displaying the selected flights in the cart.
    If a GET request is made, returns a rendered template named 'cart.html' displaying the current contents of the cart.

Modifies:
    If a POST request is made, modifies the global list variable 'flight_cart' by appending the selected flights to it.
"""

flight_cart = []
@app.route('/cart', methods=['POST', 'GET'])
def cart():
    if request.method == 'POST':
        selected_flights = request.form.getlist('flight_id')
        conn = sqlite3.connect('database/storeRecords.db')
        c = conn.cursor()

        for flight_id in selected_flights:
            c.execute("SELECT * FROM flights WHERE id=?", (flight_id,))
            flight_data = c.fetchone()
            flight_cart.append(flight_data)

        conn.close()
    
    return render_template('cart.html', cart=flight_cart)


if __name__ == '__main__':
    app.run(debug=True, host=HOST, port=PORT)
