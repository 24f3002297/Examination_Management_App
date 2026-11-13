from flask import Flask,render_template,redirect,request,url_for,session,flash
from datetime import datetime
from extensions import db
from model import *


#                                                                <----APP SETUP---->
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///Exam_nation.db"
app.config["SECRET_KEY"]="secret246"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False





db.init_app(app)

with app.app_context():
    db.create_all()  

    admin =  User.query.filter_by(email="Sanchay@gmail.com").first()
    if admin is None:
        admin = User(name="Admin",email="Sanchay@gmail.com",password="Open",role="admin")
        db.session.add(admin)
        db.session.commit()
    

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


#            <=====LOGIN=====>
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user is None:
            flash("EMAIL NOT FOUND")
            return redirect(url_for('login'))

        if user.password != password:
            flash("WRONG PASSWORD")
            return redirect(url_for('login'))
        
    

        session["user_id"] = user.id
        session["name"] = user.name

        flash("Welcome " + user.name)

        if user.role == "admin":
            return redirect(url_for('admin_dashboard'))
        elif user.role == "staff":
            return redirect(url_for('staff_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))



    return render_template("login.html")


#                    <---- SIGN UP -----> 
@app.route('/sign_up',methods=['GET','POST'])
def sign_up():

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role =  request.form.get('role')

        if password != confirm_password:
            flash("PASSWORD DONOT MATCH")
            return redirect(url_for('sign_up'))


        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("USER ALREADY EXIST")
            return redirect(url_for('sign_up'))

        new_user = User(name=name,email=email,password=password,role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created Successfully")
        return redirect(url_for('login'))



        
    return render_template("sign_up.html")

@app.route('/info')
def info():
    return render_template("info.html")



#        <====ADMIN DASHBOARD=====>
@app.route('/admin',methods=['GET','POST'])
def admin_dashboard():
    return render_template("admin.html")







































if __name__ == "__main__":
    app.run(debug=True)