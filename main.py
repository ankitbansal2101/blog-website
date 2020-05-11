from flask import Flask, render_template, request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask import json
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import math


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = "ankit-blog-secret"
app.config["UPLOAD_FOLDER"]=params["upload_location"]

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img = db.Column(db.String(12), nullable=True)
    subtitle=db.Column(db.String(50), nullable=True)
    

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    #[0: params['no_of_posts']]
    #posts = posts[]
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page= int(page)
    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    #Pagination Logic
    #First
    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)



    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)   

@app.route("/dashboard")
def dash():
    if "user" in session and session["user"]==params["admin_user"]:
        posts=Posts.query.filter_by().all()
        return render_template('dashboard.html', params=params,posts=posts)   
    else:
        return redirect("/login")    


@app.route("/uploader",methods=["GET","POST"])
def uploader():
    if "user" in session and session["user"]==params["admin_user"]:
        if request.method=="POST":
            f=request.files["file1"]
            filename=secure_filename(f.filename)
            f.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))
            return "file uploaded successfully"

from flask import send_from_directory

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'],
#                                filename)




@app.route("/edit/<string:sno>",methods=["GET","POST"])
def edit(sno):
    if "user" in session and session["user"]==params["admin_user"]:
        if request.method=="POST":
            box_title=request.form.get("title")
            box_subtitle=request.form.get("subtitle")
            box_slug=request.form.get("slug")
            box_content=request.form.get("content")
            box_img=request.form.get("image")

            if sno=="0":
                post=Posts(slug=box_slug,title=box_title,content=box_content,subtitle=box_subtitle,date=datetime.now(),img=box_img)
                db.session.add(post)
                db.session.commit()  

            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=request.form.get("title")
                post.subtitle=request.form.get("subtitle")
                post.slug=request.form.get("slug")
                post.content=request.form.get("content")
                post.img=request.form.get("image")
                post.date=datetime.now()
                post.sno=sno
                db.session.commit()
                return redirect("/dashboard")

        post=Posts.query.filter_by(sno=sno).first()

        return render_template("edit.html",params=params,post=post,sno=sno)


@app.route("/login",methods=["GET","POST"])
def login():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return redirect('/dashboard')
    if request.method=="POST":
        #REDIRECT TO ADMIN PANEL
        username=request.form.get("uname")
        userpass=request.form.get("pass")
        if (username==params["admin_user"]) and (userpass==params["admin_password"]):
            #set the session variable
            session["user"]=username
            posts=Posts.query.all()
            return redirect('/dashboard')


    return render_template('login.html', params=params)
    


@app.route("/about")
def about():
    return render_template('about.html', params=params)





@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/login")    

@app.route("/post/<string:post_slug>",methods=["GET"])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params,post=post)   


@app.route("/delete/<string:sno>",methods=["GET","POST"])
def delete(sno):
    if "user" in session and session["user"]==params["admin_user"]:
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    
        return redirect('/dashboard')
    else:
        return redirect('/login')



@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients = [params['gmail-user']],
                          body = message + "\n" + phone
                          )
    return render_template('contact.html', params=params)


app.run(debug=True)
