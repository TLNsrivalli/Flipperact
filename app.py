from flask import Flask, render_template, redirect, url_for, session, request, flash, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'flipperact'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('flipkart.html')
@app.route('/fh')
def fh():
    return render_template('FlipperactPage.html')
@app.route('/home')
def home():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM product")
    products = cur.fetchall();
    return render_template('flipkart_homepage.html', product_information = products)

@app.route('/logout')
def logout():
    session['mobile'] = None
    session['chat_friend'] = None
    return redirect('/')

@app.route('/flipperact')
def flipperact():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM flipperact_users WHERE mobile = %s", [session.get('mobile')])
    if result > 0 :
        return redirect('/flipperact_homepage')
    return render_template('/flipperact.html')

@app.route('/flipperact_homepage', methods = ['GET', 'POST'])
def flipperact_homepage():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM flipperact_users WHERE mobile = %s", [session.get('mobile')])
    personal_information = cur.fetchall();
    result = cur.execute("SELECT * FROM friends WHERE mobile = %s", [session.get('mobile')])
    friends = cur.fetchall();
    result = cur.execute("SELECT COUNT(*) FROM friends where mobile = %s", [session.get('mobile')])
    number_friends = cur.fetchall();
    birthday = []
    for i in range(0, number_friends[0]['COUNT(*)']) :
        diff = friends[i]['DOB'].month - datetime.utcnow().month
        if (diff == 0 or diff == 1) :
            difference_days = friends[i]['DOB'].day - datetime.utcnow().day
            if (difference_days <= 7 and difference_days >= 0) :
                birthday.append(friends[i]['friend_username'])
                result = cur.execute("SELECT * FROM gifts")
                gift = cur.fetchall()
                return render_template('FlipperactPage.html', information = personal_information, friends_list = friends, birthday_list = birthday, gifts = gift)
    return render_template('FlipperactPage.html', information = personal_information, friends_list = friends, birthday_list = birthday)

@app.route('/search_friends', methods = ['GET', 'POST'])
def search_friends():
    if request.method == "POST" :
        search_data = request.form['search_data']
        session['search_data'] = search_data
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM flipperact_users WHERE username like %s", [search_data])
        user_info = cur.fetchall();
        if result > 0 :
            return render_template('search_friends.html', users_info = user_info)
    return render_template('search_friends.html')

@app.route('/buygift', methods = ['GET', 'POST'])
def buygift():
    if (request.method == "POST") :
        gift_id = request.form['gift_id']
        gift_price = request.form['gift_price']
        friend_username = request.form['friend_username']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT address FROM flipperact_users where username = %s", [friend_username])
        friends_information = cur.fetchone()
        print(friends_information)
        cur.execute("INSERT INTO gifts_bought(gift_id, quantity, gift_price, mobile, address, friends_username) VALUES(%s, %s, %s, %s, %s, %s)", (gift_id, 1, gift_price, session.get('mobile'), friends_information['address'], friend_username))
        mysql.connection.commit()
        return redirect('/flipperact_homepage')


@app.route('/refertofriend', methods = ['GET', 'POST'])
def refertofriend():
    if request.method == "POST" :
        product_id = request.form['id']
        session['product_id'] = product_id;
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM friends WHERE mobile like %s", [session.get('mobile')])
        recipients_info = cur.fetchall();
        cur.close()
    return render_template('refertofriends.html', recipients = recipients_info)


@app.route('/sendtofriend', methods = ['GET', 'POST'])
def sendtofriend():
    if request.method == "POST" :
        recipient_username = request.form['recipient_username']
        recipient_mobile = request.form['recipient_mobile']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * from flipperact_users where mobile = %s", [session.get('mobile')])
        sender_details = cur.fetchall();
        sender_username = sender_details[0]['username']
        mobile = session.get('mobile')
        id = int(session['product_id'])
        result = cur.execute("INSERT INTO message(text, sendermobile, recmobile, senderusername, recusername, message_type, message_status) VALUES(%s, %s, %s, %s, %s, %s, %s)", (id, mobile, recipient_mobile, sender_username, recipient_username, "product", "Unseen"))
        mysql.connection.commit()
        cur.close()
    return redirect('/flipperact_homepage')

@app.route('/addfriend', methods = ['GET', 'POST'])
def addfriend():
    if request.method == "POST" :
        friends_username = request.form['friends_username']
        friends_mobile = request.form['friends_mobile']
        friends_DOB = request.form['friends_DOB']
        cur = mysql.connection.cursor()
        result = cur.execute("INSERT INTO friends(mobile, friend_username, friend_mobile, DOB) VALUES(%s, %s, %s, %s)", (session.get('mobile'), friends_username, friends_mobile, friends_DOB))
        mysql.connection.commit()
        cur.close()
        if result > 0 :
            return redirect('/flipperact_homepage')
    return redirect('/addfriend')

class RegisterForm(Form):
    DOB = StringField('DOB')
    username = StringField('Username', [validators.Length(min = 4, max = 25)])
    address = StringField('Address', [validators.Length(min = 3, max = 500)])

@app.route('/flipperactRegister', methods = ['GET', 'POST'])
def flipperactRegister():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        address = form.address.data
        DOB = form.DOB.data
        username = form.username.data
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO flipperact_users(mobile, username, DOB, address) VALUES(%s, %s, %s, %s)", (session.get('mobile'), username, DOB, address))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful!!', 'success')
        session['logged_in'] = True
        #session['username'] = username
        #session['name'] = name
        return redirect('/flipperact_homepage')
    return render_template('/flipperactRegister.html', form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == "POST" :
        mobile = request.form['mobile']
        password = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE mobile = %s", [mobile])
        if result > 0 :
            data = cur.fetchone()
            user_password = data['password']
            if (user_password == password) :
                session['logged_in'] = True
                session['mobile'] = mobile
                flash('You are now logged in', 'success')
                return redirect('/home')
        else :
            error = 'User name not found'
            return render_template('login.html', error=error)
            cur.close()
    return render_template('login.html')

@app.route('/chat', methods = ['GET', 'POST'])
def chat() :
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM message WHERE sendermobile or recmobile = %s", [session.get('mobile')])
    messages = cur.fetchall()
    result = cur.execute("SELECT * FROM product")
    product_information = cur.fetchall()
    for c in messages :
        if c['message_type'] == "product" :
            c['text'] = int(c['text'])
    if request.method == "POST" :
        chat_friend = request.form['chat_friend']
        session['chat_friend'] = chat_friend
    return render_template('chat.html', chat = messages, products = product_information)
@app.route('/sendmessage', methods = ['GET', 'POST'])
def sendmessage() :
    if (request.method == "POST"):
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM flipperact_users WHERE mobile = %s", [session.get('mobile')])
        user_info = cur.fetchall()
        result = cur.execute("SELECT * FROM flipperact_users WHERE username = %s", [session.get('chat_friend')])
        friend_info = cur.fetchall()
        message = request.form['message_to_send']
        recmobile = request.form['recmobile']
        senderusername = request.form['senderusername']
        recusername = request.form['recusername']
        cur = mysql.connection.cursor()
        #print(user_info[0]['username'])
        #print(friend_info[0]['mobile'])
        cur.execute("INSERT INTO message(text, sendermobile, recmobile, senderusername, recusername, message_type, message_status) VALUES(%s, %s, %s, %s, %s, %s, %s)", (message, session.get('mobile'), friend_info[0]['mobile'], user_info[0]['username'], session['chat_friend'], "text", "Unseen"))
        mysql.connection.commit()
        cur.close()
    return redirect('/chat')

@app.route('/buy', methods = ['GET', 'POST'])
def buy() :
    if (request.method == "POST") :
        product_id = request.form['product_id']
        session['product_id'] = product_id;
        return redirect('/addAddress')

@app.route('/addAddress', methods = ['GET', 'POST'])
def addAddress() :
    product_id = session.get('product_id')
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM product")
    product_information = cur.fetchall()
    #print(product_information[0])
    print(product_id)
    print(int(product_id))
    print(product_information[1]['id'])
    if (request.method == "POST") :
        address = request.form['address']
        quantity = request.form['quantity']
        cur.execute("INSERT INTO products_bought(product_id, quantity, product_price, mobile, address) VALUES(%s, %s, %s, %s, %s)", (product_id, quantity, product_information[int(product_id) - 1]['price'], session.get('mobile'), address))
        mysql.connection.commit()
        return redirect('/flipperact_homepage')
    return render_template('addAddress.html', products = product_information[int(product_id) - 1])

@app.route('/cart')
def cart() :
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM products_bought WHERE mobile = %s", [session.get('mobile')])
    cart_products = cur.fetchall()
    result = cur.execute("SELECT * FROM product")
    products_information = cur.fetchall()
    result = cur.execute("SELECT * FROM gifts_bought WHERE mobile = %s", [session.get('mobile')])
    gift_products = cur.fetchall()
    result = cur.execute("SELECT * FROM gifts")
    gifts_information = cur.fetchall()
    return render_template("cart.html", products_in_cart = cart_products, products = products_information, gifts_bought = gift_products, gifts_info = gifts_information)

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug = True)
