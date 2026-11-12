from flask import Flask,render_template,redirect,request,url_for,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from model import *


#                                                                <----APP SETUP---->
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///Exam_nation.db"
app.config["SECRET_KEY"]="secret246"
app.config["SQLALCHEMY_TRACK_MODIFICATION"]=False



db.init_app(app)
def admin_only():
    return "user_id" in session and session.get("role") == "admin"

def staff_only():
    return "user_id" in session and session.get("role") == "staff"

def user_only():
    return "user_id" in session and session.get("role") == "user"


#                                                              <----Home Screen---->
@app.route('/')
def home_page():
    return render_template("home_page.html")