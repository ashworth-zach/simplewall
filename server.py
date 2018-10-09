from flask import Flask, redirect, render_template, request, flash, session
import pymysql.cursors
import datetime
import re
from flask_bcrypt import Bcrypt        

# import the function connectToMySQL from the file mysqlconnection.py
from mysqlconnection import connectToMySQL
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
mysql = connectToMySQL("walldb")

app = Flask(__name__)
app.secret_key = "ThisIsSecret!"
bcrypt = Bcrypt(app)
@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    query='select email from users where email = %(email)s'
    data={
        'email': request.form['email']
    }
    checkvalid=mysql.query_db(query,data)
    if len(checkvalid)>0:
        flash('this email is already taken', 'erroremail')
        return redirect('/')
    if len(request.form['email']) < 1:
        flash("Email cannot be blank!", 'erroremail')
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!", 'erroremail')
        return redirect('/')
    if len(request.form['firstname']) < 1:
        flash("name cannot be blank!", 'errorfirstname')
        return redirect('/')
    if request.form['firstname'].isalpha()==False:
        flash("name cannot be contain numbers", 'errorfirstname')
        return redirect('/')
    if request.form['lastname'].isalpha()==False:
        flash("name cannot be contain numbers", 'errorlastname')
        return redirect('/')
    if len(request.form['lastname']) < 1:
        flash("last name cannot be blank!",'errorlastname')
        return redirect('/')
    if len(request.form['password']) < 8:
        flash("password must be at least 8 characters",'errorpassword')
        return redirect('/')
    if request.form['passwordconf'] != request.form['password']:
        flash("passwords do not match",'errorpasswordconf')
        return redirect('/')
    elif len(request.form['email'])>1 and EMAIL_REGEX.match(request.form['email']) and len(request.form['firstname']) > 1 and len(request.form['lastname']) > 1 and len(request.form['password']) >= 8 and request.form['passwordconf'] == request.form['password']:
        pw_hash = bcrypt.generate_password_hash(request.form['password']) 
        query='INSERT INTO users(firstname,lastname,email,password,created_at,updated_at) VALUES(%(firstname)s,%(lastname)s,%(email)s,%(password)s,now(),now())'
        data={
            'firstname': request.form['firstname'],
            'lastname': request.form['lastname'],
            'email': request.form['email'],
            'password': pw_hash
        }
        mysql.query_db(query,data)
        session['userid']=mysql.query_db('SELECT * FROM users WHERE email=%(email)s',data)
        return redirect('/thewall')
    return redirect('/')
@app.route('/login', methods=['POST'])
def login():
    query='select * from users where email = %(email)s'
    data={
        'email': request.form['email']
    }
    checkvalid=mysql.query_db(query,data)
    # print(checkvalid)
    if len(checkvalid)>0:
        flash('this email exists','erroremaillogin')
    elif len(checkvalid)==0:
        flash('this email doesnt exist','erroremaillogin')
        return redirect('/')
    if bcrypt.check_password_hash(checkvalid[0]['password'], request.form['password']) != True:
        flash('wrong password',"errorpasswordlogin")
        return redirect('/')
    elif len(checkvalid)>0 and  bcrypt.check_password_hash(checkvalid[0]['password'], request.form['password']) == True:
        session['userid']=mysql.query_db('SELECT * FROM users WHERE email=%(email)s',data)
        print(session['userid'])
        return redirect('/thewall')
    return redirect('/')
@app.route('/thewall')
def wall():
    data={
        'checkuser':session['userid'][0]['id']
    }
    allusers=mysql.query_db('select * from users where users.id !=%(checkuser)s',data)
    mymessages=mysql.query_db('select users.id,firstname,lastname,content,user_has_messages.id,user_has_messages.users_id,user_has_messages.messages_id from users join user_has_messages on users.id = user_has_messages.users_id join messages on messages.id = messages_id where user_has_messages.id = %(checkuser)s',data)
    print(mymessages)
    return render_template('/thewall.html',allusers=allusers,mymessages=mymessages)

@app.route('/send', methods=['POST'])
def sendmessage():
    data={
        'content':request.form['message'],
        'id':session['userid'][0]['id'],
    }
    x=mysql.query_db('INSERT INTO messages(content,created_at,updated_at) VALUES (%(content)s,NOW(),NOW())',data)
    print(x)
    data={
        'messageid':x,
        'id':session['userid'][0]['id'],
        'recipient':request.form['hidden']
    }
    mysql.query_db('INSERT INTO user_has_messages(users_id,messages_id,id) VALUES(%(id)s,%(messageid)s,%(recipient)s)', data)
    return redirect('/thewall')
if __name__ == "__main__":
    app.run(debug=True)