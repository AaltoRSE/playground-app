from flask import session, request, render_template, redirect, url_for
from app import app
from binascii import hexlify

current_user = ""
params = {}
users = []

def render_login():
    return render_template("login.html")

def checkloginusername():
    username = hexlify(request.form["username"].lower().strip().encode()).decode('utf-8')
    users.append(username)
    current_user = username
    return "User exists"


def checkloginpassword():
    print("hello")
    username = hexlify(request.form["username"].lower().strip().encode()).decode('utf-8')
    current_user = username
    session["username"] = username
    session["userfirstname"] = username
    if username in users:
        current_user = username
        return "correct"
    else:
        return "wrong"


def checkusername():
    username = hexlify(request.form["username"].lower().strip().encode()).decode('utf-8')
    if username not in users:
        current_user = username
        return "Available"
    else:
        return "Username taken"



@app.route('/login', methods=["GET"])
def login():
    if request.method == "GET":
        if "username" not in session:
            return render_login()
        else:
            return redirect(url_for("home"))


@app.route('/checkloginusername', methods=["POST"])
def checkUserlogin():
    return checkloginusername()


@app.route('/checkloginpassword', methods=["POST"])
def checkUserpassword():
    return checkloginpassword()


# The admin logout
@app.route('/logout', methods=["GET"])  # URL for logout
def logout():  # logout function
    session.clear()
    return redirect(url_for("home"))  # redirect to home page with message




'''def registerUser():
    fields = [k for k in request.form]
    values = [request.form[k] for k in request.form]
    data = dict(zip(fields, values))
    user_data = json.loads(json_util.dumps(data))
    user_data["password"] = getHashed(user_data["password"])
    user_data["confirmpassword"] = getHashed(user_data["confirmpassword"])
    add_user(user_data)
    print("Done")'''
