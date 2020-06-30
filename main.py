from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import os
import math
import json
from datetime import datetime

local_server = True
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USENAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    SlNo = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), unique=False, nullable=False)
    EMail = db.Column(db.String(120), nullable=False)
    Phone = db.Column(db.String(120), nullable=False)
    Mes = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(120), nullable=True)

class Post(db.Model):
    SlNo = db.Column(db.Integer, primary_key=True)
    Tittle = db.Column(db.String(80), unique=False, nullable=False)
    Slug = db.Column(db.String(120), nullable=False)
    Content = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(120), nullable=True)

@app.route("/")
def home():
    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    #Pagination Logic
    #First Page
    if(page==1):
        prev = "#"
        next = "/?page=" + str(page + 1)

    # Last Page
    elif (page == last):
         prev = "/?page=" + str(page - 1)
         next = "#"

    # Middle Page
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)



    return render_template('index.html', params = params, posts = posts, prev=prev, next=next)

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Post.query.all()
        return render_template('dashboard.html', params = params, posts = posts)

    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params['admin_user'] and userpass == params['admin_password']):
            session['user'] = username
            posts = Post.query.all()
            return render_template('login.html', params=params, posts = posts)



    return render_template('login.html', params = params)


@app.route("/about")
def about():
    return render_template('about.html', params = params)

@app.route("/post/<string:post_slug>", methods=["GET"])
def post_route(post_slug):
    post = Post.query.filter_by(Slug=post_slug).first()
    return render_template('post.html', params = params, post = post)

@app.route("/edit/<string:SlNo>", methods=["GET","POST"])
def edit (SlNo):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST' :
            box_Tittle = request.form.get('Tittle')
            Slug = request.form.get('Slug')
            Content = request.form.get('Content')
            Date = datetime.now()

            if SlNo == '0':
                post = Post(Tittle = box_Tittle, Slug = Slug, Content = Content, Date = datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Post.query.filter_by(SlNo = SlNo).first()
                post.Tittle = box_Tittle
                post.Slug = Slug
                post.Content = Content
                post.Date = Date
                db.session.commit()
                return redirect('/edit/' + SlNo)
    post = Post.query.filter_by(SlNo = SlNo).first()
    return render_template('edit.html', params = params, post = post, SlNo = SlNo)


@app.route("/delete/<string:SlNo>", methods=["GET","POST"])
def delete (SlNo):
    if ('user' in session and session['user'] == params['admin_user']):
                post = Post.query.filter_by(SlNo = SlNo).first()
                db.session.delete(post)
                db.session.commit()
    return redirect('/dashboard')



@app.route("/uploader", methods=["GET","POST"])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method =='POST'):
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        return "Uploaded Successfully"


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/contact", methods=["GET","POST"])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('Name')
        email = request.form.get('Email')
        phone = request.form.get('Phone')
        massage = request.form.get('Massage')
        Date = datetime.now()

        entry = Contacts(Name = name, EMail = email, Phone = phone, Mes = massage, Date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New massage from' + name,
                          sender = email,
                          recipients = [params['gmail-user']],
                          body = massage + "\n" + phone
                          )

    return render_template('contact.html', params = params, SlNo = SlNo)

app.run(debug=True)