from flask import Flask, render_template, request, url_for, flash, redirect
from flask import session as login_session
from flask import make_response, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import random, string, httplib2, json, requests


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Anime Catalog"

app = Flask(__name__)

engine = create_engine('postgresql+psycopg2://vagrant:1307@localhost:5432/'
                        'catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Code for getting Category Name for corresponding Category ID
@app.context_processor
def category_name_processor():
    def getCatName(cat_id):
        return session.query(Category).filter_by(id=cat_id).one().name
    return dict(getCatName=getCatName)

# Code for injecting Username into Jinja templates
@app.context_processor
def inject_username():
    return dict(username=getUsername())

# Code for injecting Categories into Jinja templates
@app.context_processor
def inject_categories():
    categories = session.query(Category)
    return dict(categories=categories)

# Code for getting the Username from login_session
def getUsername():
    if 'username' in login_session:
        return login_session['username']
    else:
        return None

# Code for getting Category ID for corresponding Category Name
def getCatId(category_name):
    a = session.query(Category).filter_by(name=category_name).first()
    if a:
        return a.id
    return None

# Code for getting Item ID for corresponding Category Name and Item Name
def getItemId(category_name, item_name):
    category_id = getCatId(category_name)
    return session.query(Item).filter_by(cat_id=category_id).filter_by(
    name=item_name).one().id

# Handles the front page of site displaying latest items
@app.route('/')
def FrontPage():
    top_items = session.query(Item).order_by(Item.created.desc())
    return render_template('index.html', top_items=top_items)

# Handles the display of items in a category
@app.route('/<string:category_name>/')
def Items(category_name):
    category_id = getCatId(category_name)
    items = session.query(Item).filter_by(cat_id=category_id)
    return render_template('items.html', items=items,
                            category_name=category_name)

# Handles the display of a specific item in a category
@app.route('/<string:category_name>/<string:item_name>/',
            methods=['GET', 'POST'])
def ItemView(category_name, item_name):
     category_id = getCatId(category_name)
     item = session.query(Item).filter_by(cat_id=category_id).filter_by(
            name=item_name).one()
     return render_template('item.html', category_name=category_name,
                             item=item)

# Handles the JSON endpoint of a specific item in a category
@app.route('/<string:category_name>/<string:item_name>/JSON',
            methods=['GET', 'POST'])
def ItemViewJSON(category_name, item_name):
     category_id = getCatId(category_name)
     item = session.query(Item).filter_by(cat_id=category_id).filter_by(
            name=item_name).one()
     return jsonify(item.serialize)

# Handles the creation of a new item in a category
@app.route('/<string:category_name>/new/', methods=['GET', 'POST'])
def NewItem(category_name):
    username = getUsername()
    if not username:
        return redirect('/login')
    if request.method == 'POST':
        category_id = getCatId(category_name)
        name = request.form['name']
        description = request.form['description']

        if session.query(Item).filter_by(cat_id=category_id).filter_by(
        name=name).first():
            error = "Item with this name already exists"
            return render_template('new_item.html',
            category_name=category_name, error=error)
        elif name and description:
            newItem = Item(name=name, username=username,
                           description=description,cat_id=category_id)
            session.add(newItem)
            session.commit()
            return render_template('item.html', category_name=category_name,
                                    item=newItem)
        else:
            error = "Name and Description need to be filled"
            return render_template('new_item.html',
            category_name=category_name, error=error)
    else:
        return render_template('new_item.html', category_name=category_name)

# Handles the editing of an existing item in a category
@app.route('/<string:category_name>/<string:item_name>/edit/',
            methods=['GET', 'POST'])
def EditItem(category_name, item_name):
    item_id = getItemId(category_name, item_name)
    item = session.query(Item).filter_by(id=item_id).one()
    if not item.username == getUsername():
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category_name = request.form['category']
        category_id = getCatId(category_name)
        if session.query(Item).filter_by(cat_id=category_id).filter_by(
        name=name).first():
            error = "Item with this name already exists"
            return render_template('edit_item.html',
            category_name=category_name, item=item, error=error)
        elif name and description and category_name:
            item.name = name
            item.description = description
            item.cat_id = category_id
            session.add(item)
            session.commit()
            return render_template('item.html', category_name=category_name,
                                    item=item)
        else:
            error = "Name, Description and Category need to be filled"
            return render_template('edit_item.html',
            category_name=category_name, item=item, error=error)
    else:
        return render_template('edit_item.html', item=item)

# Handles the deletion of an existing item in a category
@app.route('/<string:category_name>/<string:item_name>/delete/',
            methods=['GET', 'POST'])
def DeleteItem(category_name, item_name):
    item_id = getItemId(category_name, item_name)
    item = session.query(Item).filter_by(id=item_id).one()
    if not item.username == getUsername():
        return redirect('/login')
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('Items', category_name=category_name))
    else:
        return render_template('delete_item.html', item=item,
                                category_name=category_name)

# Handles the login of a User
@app.route('/login')
def showLogin():
    if getUsername():
        return redirect('/gdisconnect')
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('button.html', STATE=state)

# Helper Functions for storing login details of User
def createUser(login_session):
    newUser = User(username=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(username):
    try:
        user = session.query(User).filter_by(username=username).one()
        return user.id
    except:
        return None

# Handles login using Google OAuth
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
        return response

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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already'
                                            ' connected.'),200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['username'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash("You are now logged in as %s" % login_session['username'])
    return "You were logged in successfully"

# Handles logout from Google OAuth
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    print login_session['username']
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
    % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    # if result['status'] == '200':
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    return redirect('/')
    # else:
    	# return redirect('/')

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)