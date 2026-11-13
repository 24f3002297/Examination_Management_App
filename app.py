from flask import Flask,render_template,redirect,request,url_for,session,flash
from datetime import datetime
from extensions import db
from model import *


#                                                                <----APP SETUP---->
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///Exam_nation.db"
app.config["SECRET_KEY"]="secret246"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False



def to_date(text):
    if not text:
        return None
    return datetime.strptime(text, "%Y-%m-%d").date()




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
        session["role"] = user.role

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


#                                                                  --------------------------
#                                                                  <====ADMIN DASHBOARD=====>
#                                                                  --------------------------

#   ----------Home----------
@app.route('/admin_dashboard')
def admin_dashboard():
    if not admin_only():
        return redirect(url_for('login'))

    total_students = User.query.filter_by(role="student").count()
    total_examiners = User.query.filter_by(role="staff").count()
    pending_examiners = User.query.filter_by(role="staff", status="pending").count()
    total_courses = Course.query.count()
    total_exams = Exam.query.count()
    total_bookings = Booking.query.count()

    return render_template("admin/dashboard.html",total_students=total_students,total_examiners=total_examiners,
                           pending_examiners=pending_examiners,total_courses=total_courses,total_exams=total_exams,
                           total_bookings=total_bookings)

#   ----------COURSES ----------
@app.route('/admin/courses')
def admin_courses():
    if not admin_only():
        return redirect(url_for('login'))

    courses = Course.query.all()
    return render_template("admin/courses.html", courses=courses)

@app.route('/admin/courses/add', methods=['GET','POST'])
def add_course():
    if not admin_only():
        return redirect(url_for('login'))

    if request.method == 'POST':
        course = Course(course_code=request.form.get('course_code'),
                        course_name=request.form.get('course_name'),
                        description=request.form.get('description'),
                        status=request.form.get('status'))
        db.session.add(course)
        db.session.commit()
        flash("Course added")
        return redirect(url_for('admin_courses'))

    return render_template("admin/course_form.html", course=None)

@app.route('/admin/courses/edit/<int:course_id>', methods=['GET','POST'])
def edit_course(course_id):
    if not admin_only():
        return redirect(url_for('login'))

    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        course.course_code = request.form.get('course_code')
        course.course_name = request.form.get('course_name')
        course.description = request.form.get('description')
        course.status = request.form.get('status')
        db.session.commit()
        flash("Course updated")
        return redirect(url_for('admin_courses'))

    return render_template("admin/course_form.html", course=course)

@app.route('/admin/courses/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if not admin_only():
        return redirect(url_for('login'))

    course = Course.query.get_or_404(course_id)

    # a course that has exams cannot be deleted
    if len(course.exams) > 0:
        flash("Cannot delete: this course has exams. Set it to inactive instead")
        return redirect(url_for('admin_courses'))

    db.session.delete(course)
    db.session.commit()
    flash("Course deleted")
    return redirect(url_for('admin_courses'))


#   ---------- 3. EXAMS ----------
@app.route('/admin/exams')
def admin_exams():
    if not admin_only():
        return redirect(url_for('login'))

    exams = Exam.query.all()
    return render_template("admin/exams.html", exams=exams)

@app.route('/admin/exams/add', methods=['GET','POST'])
def add_exam():
    if not admin_only():
        return redirect(url_for('login'))

    courses = Course.query.filter_by(status="active").all()

    if request.method == 'POST':
        start = to_date(request.form.get('exam_start_date'))
        end = to_date(request.form.get('exam_end_date'))

        if end < start:
            flash("End date cannot be before start date")
            return redirect(url_for('add_exam'))

        exam = Exam(course_id=int(request.form.get('course_id')),
                    exam_name=request.form.get('exam_name'),
                    exam_type=request.form.get('exam_type'),
                    max_marks=float(request.form.get('max_marks')),
                    exam_start_date=start,
                    exam_end_date=end)
        db.session.add(exam)
        db.session.commit()
        flash("Exam added")
        return redirect(url_for('admin_exams'))

    return render_template("admin/exam_form.html", exam=None, courses=courses)

@app.route('/admin/exams/edit/<int:exam_id>', methods=['GET','POST'])
def edit_exam(exam_id):
    if not admin_only():
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    courses = Course.query.all()

    if request.method == 'POST':
        start = to_date(request.form.get('exam_start_date'))
        end = to_date(request.form.get('exam_end_date'))

        if end < start:
            flash("End date cannot be before start date")
            return redirect(url_for('edit_exam', exam_id=exam_id))

        exam.course_id = int(request.form.get('course_id'))
        exam.exam_name = request.form.get('exam_name')
        exam.exam_type = request.form.get('exam_type')
        exam.max_marks = float(request.form.get('max_marks'))
        exam.exam_start_date = start
        exam.exam_end_date = end
        db.session.commit()
        flash("Exam updated")
        return redirect(url_for('admin_exams'))

    return render_template("admin/exam_form.html", exam=exam, courses=courses)

@app.route('/admin/exams/delete/<int:exam_id>', methods=['POST'])
def delete_exam(exam_id):
    if not admin_only():
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

    # an exam that has slots cannot be deleted
    if len(exam.slots) > 0:
        flash("Cannot delete: this exam already has slots")
        return redirect(url_for('admin_exams'))

    # delete its rubrics first, then the exam
    for r in exam.rubrics:
        db.session.delete(r)
    db.session.delete(exam)
    db.session.commit()
    flash("Exam deleted")
    return redirect(url_for('admin_exams'))


#   ---------- 4. RUBRICS ----------
# list of exams, click one to manage its rubrics
@app.route('/admin/rubrics')
def admin_rubrics():
    if not admin_only():
        return redirect(url_for('login'))

    exams = Exam.query.all()
    return render_template("admin/rubrics_exams.html", exams=exams)

@app.route('/admin/rubrics/<int:exam_id>', methods=['GET','POST'])
def manage_rubrics(exam_id):
    if not admin_only():
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

    # total weightage already used
    total = 0
    for r in exam.rubrics:
        total = total + r.weightage

    if request.method == 'POST':
        weightage = float(request.form.get('weightage'))

        if total + weightage > 100:
            flash("Total weightage cannot go above 100")
            return redirect(url_for('manage_rubrics', exam_id=exam_id))

        rubric = ExaminationRubric(exam_id=exam_id,
                                   criterion_name=request.form.get('criterion_name'),
                                   weightage=weightage,
                                   description=request.form.get('description'))
        db.session.add(rubric)
        db.session.commit()
        flash("Rubric added")
        return redirect(url_for('manage_rubrics', exam_id=exam_id))

    return render_template("admin/rubrics.html", exam=exam, total=total)

@app.route('/admin/rubrics/edit/<int:rubric_id>', methods=['GET','POST'])
def edit_rubric(rubric_id):
    if not admin_only():
        return redirect(url_for('login'))

    rubric = ExaminationRubric.query.get_or_404(rubric_id)

    if request.method == 'POST':
        weightage = float(request.form.get('weightage'))

        # total of the OTHER rubrics of this exam
        others = 0
        for r in rubric.exam.rubrics:
            if r.rubric_id != rubric.rubric_id:
                others = others + r.weightage

        if others + weightage > 100:
            flash("Total weightage cannot go above 100")
            return redirect(url_for('edit_rubric', rubric_id=rubric_id))

        rubric.criterion_name = request.form.get('criterion_name')
        rubric.weightage = weightage
        rubric.description = request.form.get('description')
        db.session.commit()
        flash("Rubric updated")
        return redirect(url_for('manage_rubrics', exam_id=rubric.exam_id))

    return render_template("admin/rubric_edit.html", rubric=rubric)

@app.route('/admin/rubrics/delete/<int:rubric_id>', methods=['POST'])
def delete_rubric(rubric_id):
    if not admin_only():
        return redirect(url_for('login'))

    rubric = ExaminationRubric.query.get_or_404(rubric_id)
    exam_id = rubric.exam_id
    db.session.delete(rubric)
    db.session.commit()
    flash("Rubric deleted")
    return redirect(url_for('manage_rubrics', exam_id=exam_id))


#   ---------- 5. EXAMINERS ----------
@app.route('/admin/examiners')
def admin_examiners():
    if not admin_only():
        return redirect(url_for('login'))

    staff_list = User.query.filter_by(role="staff").all()

    # pair every examiner with his profile (profile can be None)
    rows = []
    for u in staff_list:
        profile = ExaminerProfile.query.filter_by(examiner_id=u.id).first()
        rows.append({"user": u, "profile": profile})

    return render_template("admin/examiners.html", rows=rows)

# approve / deactivate / activate  (new_status = active or inactive)
@app.route('/admin/examiners/status/<int:user_id>/<new_status>', methods=['POST'])
def change_examiner_status(user_id, new_status):
    if not admin_only():
        return redirect(url_for('login'))

    if new_status not in ["active", "inactive"]:
        flash("Wrong status")
        return redirect(url_for('admin_examiners'))

    user = User.query.get_or_404(user_id)

    if user.role != "staff":
        flash("This user is not an examiner")
        return redirect(url_for('admin_examiners'))

    user.status = new_status
    db.session.commit()
    flash(user.name + " is now " + new_status)
    return redirect(url_for('admin_examiners'))

@app.route('/admin/examiners/add', methods=['GET','POST'])
def add_examiner():
    if not admin_only():
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form.get('email')

        if User.query.filter_by(email=email).first():
            flash("USER ALREADY EXIST")
            return redirect(url_for('add_examiner'))

        # admin creates the examiner, so he is active at once
        user = User(name=request.form.get('name'),
                    email=email,
                    password=request.form.get('password'),
                    role="staff",
                    status="active")
        db.session.add(user)
        db.session.commit()      # commit first so user.id is created

        profile = ExaminerProfile(examiner_id=user.id,
                                  phone=request.form.get('phone'),
                                  qualification=request.form.get('qualification'),
                                  experience=int(request.form.get('experience')),
                                  department=request.form.get('department'))
        db.session.add(profile)
        db.session.commit()

        flash("Examiner added")
        return redirect(url_for('admin_examiners'))

    return render_template("admin/examiner_form.html")


#   ---------- 6. TIMELINES + OPEN / CLOSE SWITCHES ----------
@app.route('/admin/timelines')
def admin_timelines():
    if not admin_only():
        return redirect(url_for('login'))

    exams = Exam.query.all()
    return render_template("admin/timelines.html", exams=exams)

@app.route('/admin/timelines/<int:exam_id>', methods=['POST'])
def save_timeline(exam_id):
    if not admin_only():
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    exam.slot_creation_deadline = to_date(request.form.get('slot_creation_deadline'))
    exam.booking_deadline = to_date(request.form.get('booking_deadline'))
    db.session.commit()
    flash("Timeline saved")
    return redirect(url_for('admin_timelines'))

@app.route('/admin/toggle_slot_creation/<int:exam_id>', methods=['POST'])
def toggle_slot_creation(exam_id):
    if not admin_only():
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    exam.slot_creation_open = not exam.slot_creation_open     # flip True/False
    db.session.commit()
    flash("Slot creation changed")
    return redirect(url_for('admin_timelines'))

@app.route('/admin/toggle_booking/<int:exam_id>', methods=['POST'])
def toggle_booking(exam_id):
    if not admin_only():
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    exam.booking_open = not exam.booking_open
    db.session.commit()
    flash("Student booking changed")
    return redirect(url_for('admin_timelines'))


#   ---------- 7. SLOTS (view all + change examiner) ----------
@app.route('/admin/slots')
def admin_slots():
    if not admin_only():
        return redirect(url_for('login'))

    exams = Exam.query.all()
    exam_id = request.args.get('exam_id')      # filter from the dropdown

    if exam_id:
        slots = ExamSlot.query.filter_by(exam_id=int(exam_id)).all()
    else:
        slots = ExamSlot.query.all()

    return render_template("admin/slots.html", slots=slots, exams=exams, exam_id=exam_id)

@app.route('/admin/slots/<int:slot_id>/examiner', methods=['GET','POST'])
def change_examiner(slot_id):
    if not admin_only():
        return redirect(url_for('login'))

    slot = ExamSlot.query.get_or_404(slot_id)
    examiners = User.query.filter_by(role="staff", status="active").all()

    if request.method == 'POST':
        new_id = int(request.form.get('examiner_id'))

        # does this examiner already have another slot at the same time?
        other_slots = ExamSlot.query.filter_by(examiner_id=new_id, date=slot.date).all()
        for s in other_slots:
            if s.slot_id != slot.slot_id and s.start_time < slot.end_time and s.end_time > slot.start_time:
                flash("This examiner already has a slot at that time")
                return redirect(url_for('change_examiner', slot_id=slot_id))

        slot.examiner_id = new_id
        db.session.commit()
        flash("Examiner changed")
        return redirect(url_for('admin_slots'))

    return render_template("admin/slot_examiner.html", slot=slot, examiners=examiners)


#   ---------- 8. BOOKINGS (view all + reschedule) ----------
@app.route('/admin/bookings')
def admin_bookings():
    if not admin_only():
        return redirect(url_for('login'))

    bookings = Booking.query.all()
    return render_template("admin/bookings.html", bookings=bookings)

@app.route('/admin/bookings/<int:booking_id>/reschedule', methods=['GET','POST'])
def reschedule_booking(booking_id):
    if not admin_only():
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)
    old_slot = booking.slot

    # other slots of the SAME exam that still have seats
    other_slots = ExamSlot.query.filter(ExamSlot.exam_id == old_slot.exam_id,
                                        ExamSlot.slot_id != old_slot.slot_id,
                                        ExamSlot.available_seats > 0).all()

    if request.method == 'POST':
        new_slot = ExamSlot.query.get_or_404(int(request.form.get('slot_id')))

        if new_slot.available_seats <= 0:
            flash("No seats left in that slot")
            return redirect(url_for('reschedule_booking', booking_id=booking_id))

        old_slot.available_seats = old_slot.available_seats + 1     # give the old seat back
        new_slot.available_seats = new_slot.available_seats - 1     # take a seat in the new slot
        booking.slot_id = new_slot.slot_id
        db.session.commit()

        flash("Booking rescheduled")
        return redirect(url_for('admin_bookings'))

    return render_template("admin/reschedule.html", booking=booking, other_slots=other_slots)


#   ---------- 9. VIEW ALL STUDENTS ----------
@app.route('/admin/students')
def admin_students():
    if not admin_only():
        return redirect(url_for('login'))

    students = User.query.filter_by(role="student").all()
    return render_template("admin/students.html", students=students)


#   ---------- 10. SEARCH ----------
@app.route('/admin/search')
def admin_search():
    if not admin_only():
        return redirect(url_for('login'))

    search_type = request.args.get('type')
    q = request.args.get('q', '').strip()

    students = []
    examiners = []
    exams = []
    bookings = []

    if q:
        if search_type == "student":
            query = User.query.filter_by(role="student")
            if q.isdigit():
                students = query.filter(User.id == int(q)).all()
            else:
                students = query.filter(User.name.ilike("%" + q + "%")).all()

        elif search_type == "examiner":
            query = User.query.filter_by(role="staff")
            if q.isdigit():
                examiners = query.filter(User.id == int(q)).all()
            else:
                examiners = query.filter(User.name.ilike("%" + q + "%")).all()

        elif search_type == "exam":
            if q.isdigit():
                exams = Exam.query.filter(Exam.exam_id == int(q)).all()
            else:
                exams = Exam.query.filter(Exam.exam_name.ilike("%" + q + "%")).all()

        elif search_type == "booking":
            if q.isdigit():
                bookings = Booking.query.filter(Booking.booking_id == int(q)).all()
            else:
                # search bookings by the student's name
                bookings = Booking.query.join(User, Booking.student_id == User.id).filter(User.name.ilike("%" + q + "%")).all()

    return render_template("admin/search.html", search_type=search_type, q=q,
                           students=students, examiners=examiners,
                           exams=exams, bookings=bookings)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))





































if __name__ == "__main__":
    app.run(debug=True)