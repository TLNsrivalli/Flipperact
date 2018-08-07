from flask import Flask, render_template, redirect, url_for, session, request, flash, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask_mysqldb import MySQL

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

@app.route('/home')
def home():
    return render_template('home.html')

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
    if request.method == "POST" :
        search_data = request.form['search_data']
        session['search_data'] = search_data
        return redirect('/search_friends')
    return render_template('flipperact_homepage.html', information = personal_information, friends_list = friends)

@app.route('/search_friends', methods = ['GET', 'POST'])
def search_friends():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM flipperact_users WHERE username like %s", [session.get('search_data')])
    user_info = cur.fetchall();
    if result > 0 :
        return render_template('search_friends.html', users_info = user_info)
    return render_template('search_friends.html', error=error)

@app.route('/addfriend', methods = ['GET', 'POST'])
def addfriend():
    if request.method == "POST" :
        friends_username = request.form['friends_username']
        friends_mobile = request.form['friends_mobile']
        cur = mysql.connection.cursor()
        result = cur.execute("INSERT INTO friends(mobile, friend_username, friend_mobile) VALUES(%s, %s, %s)", (session.get('mobile'), friends_username, friends_mobile))
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

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug = True)
