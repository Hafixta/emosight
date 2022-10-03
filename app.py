from engine import training
import csv
import pickle
import pandas as pd
from flask import Flask, render_template, url_for, request, session, redirect, flash, make_response
import os
from flask_pymongo import PyMongo
from flask_mail import Mail, Message
import re
import nltk
import create_db
from password_strength import PasswordPolicy
from password_strength import PasswordStats
import random


app = Flask(__name__)
app.secret_key = "testing"
app.config["SECRET_KEY"]
#configuration of ComosDb in the Azure
app.config['MONGO_URI'] = "mongodb://emosight:j5R1LYFyPkzkNz7csvGqtzcAphbJE8zd3ViR7TcoenEL78Up5gRS2KB7Xqf7tzz4KbKnTngi9Rp7e4pqPga2RQ==@emosight.mongo.cosmos.azure.com:10255/register_users?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@emosight@"
mongo = PyMongo(app)
reg_users = mongo




app.config['MAIL_DEBUG'] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'netmobilefix@gmail.com'
app.config['MAIL_PASSWORD'] = 'troewcsmtyqyvkdk'
mail = Mail(app)


sentiment_model = training()

def sendContactForm(result):
    msg = Message("Contact Form from Emosight",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=["alivealive909@gmail.com", "hafixta@gmail.com "])

    msg.body = """
    Hello there,
    You just received a contact form.
    Name: {}
    Email: {}
    Message: {}
    regards,
    Webmaster
    """.format(result['name'], result['email'], result['message'])

    mail.send(msg)


@app.route('/')
def index():
    return render_template('main.html')


@app.route('/user_login', methods=['POST'])
def login_user():
    user_collection = mongo.db.register_users
    print('user collection', user_collection)
    if request.method == 'POST':
        print('yesssss')
        username = request.form['email']
        password = request.form['password']
        login_user = user_collection.find_one({'email': username})

        if login_user:
            if login_user['password'] == password:
                session['email'] = username
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html')

        return render_template('login.html')


policy = PasswordPolicy.from_names(
    length=8,  # min length: 8
    uppercase=1,  # need min. 2 uppercase letters
    numbers=1,  # need min. 2 digits
    strength=0.66 # need a password that scores at least 0.5 with its entropy bits
)
app.config['SECRET_KEY'] = '@#$%^&*('
@app.route('/user_signup', methods=['POST'])
def signup_user():
    user_collection = mongo.db.register_users
    if request.method == 'POST':
        user = request.form["email"]
        pwd = request.form["password"]
        stats = PasswordStats(pwd)
        checkpolicy = policy.test(pwd)
        existing_user = user_collection.find_one({'email': user})
        if existing_user is None:
            user_collection.insert_one({'email': user, 'password': pwd})
            session['email'] = request.form['email']
            return redirect(url_for('dashboard'))
        else:
            return "user already exists"


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/results', methods=['POST', 'GET'])
def model_result():
    return render_template('download.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')


@app.route('/contact', methods=["GET","POST"])
def contact():
    data = {"msg": ""}
    if request.method == 'POST':
        result = {}
        
        result['name'] = request.form['name']
        result['email'] = request.form['email'].replace(' ', '').lower()
        result['message'] = request.form['message']

        sendContactForm(result)
        print(result)
        data = {"msg": "Your Form is submitted successfully!"}


    return render_template('contact.html', data=data)


@app.route('/emosight')
def emosight():
    return render_template('emosight.html')


@app.route('/upload')
def upload():
    return render_template('upload.html')


@app.route('/download')
def download():
    return render_template('download.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        randNo = random.randint(100000, 999999)
        session['code'] = randNo
        session['email'] = email
        msg = Message('reset code', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = str(randNo)
        mail.send(msg)
        return render_template('newpassword.html')

    return render_template('forgot.html')

@app.route('/new_pass', methods=['GET', 'POST'])
def new_password():
    user_collection = mongo.db.register_users
    if request.method == 'POST':
        if str(request.form['code']) == str(session['code']):
            filter = { 'email': session['email']  }
            # Values to be updated.
            newvalues = { "$set": { 'password': request.form['newpassword'] } }
            
            # Using update_one() method for single
            # updation.
            user_collection.update_one(filter, newvalues)
    
            return redirect(url_for('dashboard'))

        return make_response("Some error while resetting")
    return render_template("forgot.html")


@app.route('/datafile', methods=['GET', 'POST'])
def uploadfile():

    if request.method == 'POST':
        if request.files:
            uploaded_file = request.files['csvfile']

            #uploading CSV or Excel file
            if 'csv' in str(uploaded_file):
                df = pd.read_csv(uploaded_file)
            elif 'xlsx' in str(uploaded_file):
                df = pd.read_excel(uploaded_file)
            else:
                return redirect(url_for('upload'))


            
            coloms = df.columns
            print('coloms are:', coloms)
            df['text'] = df[coloms[1]]
            print('text is::::', df['text'])

            #Printing Clean Text in new file
            df['clean_text'] = df['text'].apply(sentiment_model.clean_text)
            print('clean text:', df['clean_text'])

            #printing new column of sentiments in the file by applying sentimental model on the clean text
            df['sentiment'] = df['clean_text'].apply(
                sentiment_model.sentiment_scores)
            #cleaning the dates
            df['UTCC'] = pd.to_datetime(df["UTC"]).dt.strftime("%Y-%m-%d")

            df.to_csv('static/file/results2.csv')
            #creating variables to print the graph
            tmp = df['sentiment'].value_counts()
            x1 = list(tmp.index)
            y = list((tmp.values/tmp.values.sum())*100)

            #Grouping the Sentiments according to the dates
            df = df.sort_values('UTCC').groupby(['UTCC','sentiment']).size()

            indexes = list(set([x[0] for x in df.index]))

            indexes = df[: , 'Positive'].index.values

            #Getting values for Negative, Positive and Neutral
            neg = {}
            pos = {}
            net = {}
            for x in indexes:
                if x in df[: , 'Negative'].index:
                    idx = list(df[: , 'Negative'].index).index(x)
                    neg[x] =  df[: , 'Negative'].values[idx] 
                else:
                    neg[x] =  0

                if x in df[: , 'Positive'].index:
                    idx = list(df[: , 'Positive'].index).index(x)
                    pos[x] =  df[: , 'Positive'].values[idx] 
                else:
                    pos[x] =  0


                if x in df[: , 'Neutral'].index:
                    idx = list(df[: , 'Neutral'].index).index(x)
                    net[x] =  df[: , 'Neutral'].values[idx] 
                else:
                    net[x] =  0
            #Sorting values for Negative, Neutral and Positive variables
            labels = list(dict(sorted(neg.items(), key=lambda item: item[0])).keys())
            neg = list(dict(sorted(neg.items(), key=lambda item: item[0])).values())
            net = list(dict(sorted(net.items(), key=lambda item: item[0])).values())
            pos = list(dict(sorted(pos.items(), key=lambda item: item[0])).values())
            

    
    return render_template('charts.html', x1=x1, y=y, 
                            nvalues=neg,
							nlabels=labels,
							ncolor='rgba(255, 99, 132, 0.9)',
							gvalues=net,
							glabels=labels,
							gcolor='rgba(255, 206, 86, 0.9)',
							wvalues=pos,
							wlabels=labels,
							wcolor='rgba(54, 162, 235, 0.9)')



if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(host='0.0.0.0', port=5000)
