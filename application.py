#POWERSHELL 
#  $env:FLASK_APP = "application.py"  
#  $env:FLASK_ENV = "development" 
#  $env:FLASK_DEBUG=0
#CMD 
#  set FLASK_APP=application.py 
#  set FLASK_ENV=development 
#  set FLASK_DEBUG=0
#Linux,Mac 
#  export FLASK_APP=application.py 
#  export FLASK_ENV=development 
#  export FLASK_DEBUG=0

import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///EAD.db")

@app.route("/")
@login_required
def index():
    return render_template("index.html",
       message=session['messageOfIndexPage'])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html",message_error="You must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html",message_error="You must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html",message_error="Invalid username/password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session['messageOfIndexPage'] = "Log in"

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    session['messageOfIndexPage'] = "Log out"
    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        #Get information of Form and verify if any of them is Null
        username = request.form.get("username")
        password = request.form.get("password")
        passwordAgain = request.form.get("password_again")
        image = request.form.get("image")
        about = request.form.get("about")

        # Ensure username was submitted
        if not username:
            return render_template("register.html", message_error="You must provide username")
        
        #Ensure image was submitted
        elif not image:
            return render_template("register.html", message_error="You must provide a link of image")

        #Ensure about was submitted
        elif not about:
            return render_template("register.html", message_error="You must provide an description")

        # Ensure password was submitted
        elif not password or not passwordAgain:
            return render_template("register.html", message_error="You must provide password")

        #Ensure passwords are equal
        elif password != passwordAgain:
            return render_template("register.html", message_error="The passwords are not equal")

        #Verify if user already exists
        userAlreadyExists = db.execute("SELECT * FROM users WHERE username = :username",
        username=username)

        if(len(userAlreadyExists) == 1):
            return render_template("register.html", message_error="That name is already in use")

        # Registring user
        db.execute("INSERT INTO users (username,hash,level,image,about) VALUES(:username,:hashpassword,1,:image,:about); ",
        username=username,hashpassword=generate_password_hash(password),image=image,about=about)

        # Taking user id to the session
        user = db.execute('SELECT * FROM users WHERE username = :username',username=username)[0]
        session["user_id"] = user["id"]
        session['messageOfIndexPage'] = 'Registered!'
        return redirect('/')
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/perfil",methods=["GET", "POST"])
@login_required
def perfil():
    aboutUser = db.execute('SELECT * FROM users WHERE id = :userId',userId=session["user_id"])[0]
    if request.method == "POST":
        username = request.form.get("username")
        image = request.form.get("image")
        about = request.form.get("about")
        
        if not username:
            return render_template("perfil.html", message_error="You must provide a username",aboutUser=aboutUser)
        elif not image:
            return render_template("perfil.html", message_error="You must provide a link of image",aboutUser=aboutUser)
        elif not about:
            return render_template("perfil.html", message_error="You must provide a description",aboutUser=aboutUser)

        db.execute('UPDATE users SET username=:username, image=:image, about=:about  WHERE id = :userId '
        ,userId=session['user_id'],username=username,image=image,about=about)

        session['messageOfIndexPage'] = None
        return redirect('/')
    else:
        return render_template("perfil.html",aboutUser=aboutUser)

@app.route("/create_category", methods=["GET", "POST"])
@login_required
def create_category():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return render_template("create_category.html", message_error="You must provide a name")

        #Verify if that category already exists
        category = db.execute('SELECT * FROM categories WHERE name = :name',name=name)
        if(len(category) == 1):
            return render_template("create_category.html", message_error="That category already exists")

        db.execute('INSERT INTO categories (name,user_id) VALUES (:name,:user_id)',name=name,user_id=session['user_id'])
        session['messageOfIndexPage'] = 'You have create a new category: ' + name
        return redirect('/')
    else:
        return render_template("create_category.html")

@app.route("/create_video",methods=["GET", "POST"])
@login_required
def create_video():
    categories = db.execute('SELECT name FROM categories')
    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        link = request.form.get("link")
        
        if not name:
            return render_template("create_video.html", message_error="You must provide a name",categories=categories)
        elif not category:
            return render_template("create_video.html", message_error="You must provide a category",categories=categories)
        elif not link:
            return render_template("create_video.html", message_error="You must provide a link",categories=categories)
        
        videos = db.execute('SELECT * FROM videos WHERE name=:name',name=name)
        if len(videos) == 1:
            return render_template("create_video.html", message_error="That video already exists",categories=categories)

        db.execute('INSERT INTO videos (link,name,category) VALUES(:link,:name,:category)',
        link=link,name=name,category=category)

        session['messageOfIndexPage'] = 'You have create a new video: ' + name
        return redirect('/')
    else:
        return render_template("create_video.html",categories=categories)

@app.route("/explore")
@login_required
def explore():
    videos = db.execute('SELECT * FROM videos')
    return render_template("explore.html",videos=videos)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
    
