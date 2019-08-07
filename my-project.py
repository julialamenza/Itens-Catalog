from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Bar, MenuItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app=Flask(__name__,template_folder='templates')


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "My new bar"


# Connect to Database and create database session
engine = create_engine('sqlite:///barmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output

@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session.get('credentials')
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session





# JSON APIs to view Bar Information
@app.route('/bar/<int:bar_id>/menu/JSON')
def barMenu(bar_id):
    bar = session.query(Bar).filter_by(id=bar_id).one()
    items = session.query(MenuItem).filter_by(
        bar_id=bar_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/bar/<int:bar_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(bar_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/bar/JSON')
def barsJSON():
    bars = session.query(Bar).all()
    return jsonify(bars=[r.serialize for r in bars])


# Show all bars
@app.route('/')
@app.route('/bar/')
def showBars():
    bars = session.query(Bar).order_by(asc(Bar.name))
    if 'username' not in login_session:
        return render_template('publicBars.html', bars=bars)
    else:
        return render_template('bars.html', bars=bars)

# Create a new bar


@app.route('/bar/new/', methods=['GET', 'POST'])
def newBar():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newBar = Bar(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newBar)
        flash('New Bar %s Successfully Created' % newBar.name)
        session.commit()
        return redirect(url_for('showBars'))
    else:
        return render_template('newBar.html')

# Edit a Bar


@app.route('/bar/<int:bar_id>/edit/', methods=['GET', 'POST'])
def editBar(bar_id):
    editedBar = session.query(
        Bar).filter_by(id=bar_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedBar.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this bar. Please create your own bar in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedBar.name = request.form['name']
            flash('Bar Successfully Edited %s' % editedBar.name)
            return redirect(url_for('showBars'))
    else:
        return render_template('editBar.html', bar=editedBar)


# Delete a Bar
@app.route('/bar/<int:bar_id>/delete/', methods=['GET', 'POST'])
def deleteBar(bar_id):
    barToDelete = session.query(
        Bar).filter_by(id=bar_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if barToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this bar. Please create your own bar in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(barToDelete)
        flash('%s Successfully Deleted' % barToDelete.name)
        session.commit()
        return redirect(url_for('showbars', Bar_id=bar_id))
    else:
        return render_template('deleteBar.html', bar=barToDelete)

# Show a bar menu


@app.route('/bar/<int:bar_id>/')
@app.route('/bar/<int:bar_id>/menu/')
def showMenu(bar_id):
    bar = session.query(Bar).filter_by(id=bar_id).one()
    creator = getUserInfo(bar.user_id)
    items = session.query(MenuItem).filter_by(
        bar_id=bar_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicMenu.html', items=items, bar=bar, creator=creator)
    else:
        return render_template('menu.html', items=items, bar=bar, creator=creator)


# Create a new menu item
@app.route('/bar/<int:bar_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(bar_id):
    if 'username' not in login_session:
        return redirect('/login')
    bar = session.query(Bar).filter_by(id=bar_id).one()
    if login_session['user_id'] != bar.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add menu items to this bar. Please create your own bar in order to add items.');}</script><body onload='myFunction()''>"
        if request.method == 'POST':
            newItem = MenuItem(name=request.form['name'], description=request.form['description'], price=request.form[
                               'price'], course=request.form['course'], bar_id=bar_id, user_id=bar.user_id)
            session.add(newItem)
            session.commit()
            flash('New Menu %s Item Successfully Created' % (newItem.name))
            return redirect(url_for('showMenu', bar_id=bar_id))
    else:
        return render_template('newMenuItem.html', bar_id=bar_id)

# Edit a menu item


@app.route('/bar/<int:bar_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def editMenuItem(bar_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    bar = session.query(Bar).filter_by(id=bar_id).one()
    if login_session['user_id'] != bar.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit menu items to this bar. Please create your own bar in order to edit items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.course = request.form['course']
        session.add(editedItem)
        session.commit()
        flash('Menu Item Successfully Edited')
        return redirect(url_for('showMenu', bar_id=bar_id))
    else:
        return render_template('editMenuItem.html', bar_id=bar_id, menu_id=menu_id, item=editedItem)


# Delete a menu item
@app.route('/bar/<int:bar_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(bar_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    bar = session.query(Bar).filter_by(id=bar_id).one()
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if login_session['user_id'] != bar.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete menu items to this bar. Please create your own bar in order to delete items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showMenu', bar_id=bar_id))
    else:
        return render_template('deleteMenuItem.html', item=itemToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        flash("You have successfully been logged out.")
        return redirect(url_for('showbars'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showBars'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='localhost', port=5000)
