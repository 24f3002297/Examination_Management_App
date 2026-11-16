from flask import Flask,render_template,redirect,request,url_for,session,flash
from datetime import datetime, date
from sqlalchemy import or_, func
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

def to_time(text):
    if not text:
        return None
    return datetime.strptime(text[:5], "%H:%M").time()


def go(page, anchor="", **kw):
    return redirect(url_for(page, **kw) + "#" + anchor)




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

def student_only():
    return "user_id" in session and session.get("role") == "student"

def staff_only():
    # examiner must be logged in AND approved by the admin
    if "user_id" not in session or session.get("role") != "staff":
        return False
    user = db.session.get(User, session["user_id"])
    return user is not None and user.status == "active"


#                                                              <----Home Screen---->
@app.route('/')
def home_page():
    return render_template("home_page.html")


#                                                            <=====LOGIN=====>
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter(func.lower(User.email) == email.lower()).first()

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


#                                                            <---- SIGN UP -----> 
@app.route('/sign_up',methods=['GET','POST'])
def sign_up():

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        
        if role not in ["student", "staff"]:
            flash("Please choose a valid account type")
            return redirect(url_for('sign_up'))

        if not name or not email or not password:
            flash("Please fill all required fields")
            return redirect(url_for('sign_up'))

        if password != confirm_password:
            flash("PASSWORD DONOT MATCH")
            return redirect(url_for('sign_up'))


        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("USER ALREADY EXIST")
            return redirect(url_for('sign_up'))

        
        account_status = "active" if role == "student" else "pending"
        new_user = User(name=name, email=email, password=password,role=role, status=account_status)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created Successfully")
        return redirect(url_for('login'))



        
    return render_template("sign_up.html")

@app.route('/info')
def info():
    return render_template("info.html")


#                                                                  --------------------------
#                                                                  <====ADMIN PORTAL=====>
#                                                                  --------------------------

#                                                             ---------- Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if not admin_only():
        return redirect(url_for('login'))

    examiners = User.query.filter_by(role="staff").all()
    pending = [u for u in examiners if u.status == "pending"]
    exams = Exam.query.all()

    stats = [("Students", User.query.filter_by(role="student").count()),
             ("Examiners", len(examiners)),
             ("Waiting for approval", len(pending)),
             ("Courses", Course.query.count()),
             ("Exams", len(exams)),
             ("Slots", ExamSlot.query.count()),
             ("Bookings", Booking.query.count())]

    latest = Booking.query.order_by(Booking.booking_id.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, pending=pending, latest=latest, exams=exams)


#                                                    ---------- Courses ----------
@app.route('/admin/courses')
def admin_courses():
    if not admin_only():
        return redirect(url_for('login'))

    return render_template("admin/courses.html", courses=Course.query.all())


@app.route('/admin/courses/form', defaults={'course_id': 0}, methods=['GET','POST'])
@app.route('/admin/courses/form/<int:course_id>', methods=['GET','POST'])
def admin_course_form(course_id):
    if not admin_only():
        return redirect(url_for('login'))

    course = None
    if course_id:
        course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        if course is None:
            course = Course()
            db.session.add(course)
        course.course_code = request.form.get('course_code')
        course.course_name = request.form.get('course_name')
        course.description = request.form.get('description')
        course.status = request.form.get('status')
        db.session.commit()
        flash("Course saved")
        return redirect(url_for('admin_courses'))

    return render_template("admin/course_form.html", course=course)

@app.route('/admin/courses/delete/<int:course_id>', methods=['POST'])
def admin_course_delete(course_id):
    if not admin_only():
        return redirect(url_for('login'))

    course = Course.query.get_or_404(course_id)
    if len(course.exams) > 0:
        flash("Cannot delete: this course has exams. Set it to inactive instead")
    else:
        db.session.delete(course)
        db.session.commit()
        flash("Course deleted")
    return redirect(url_for('admin_courses'))

#                                                                          Exams 
@app.route('/admin/exams')
def admin_exams():
    if not admin_only():
        return redirect(url_for('login'))

    return render_template("admin/exams.html", exams=Exam.query.all())

@app.route('/admin/exams/form', defaults={'exam_id': 0}, methods=['GET','POST'])
@app.route('/admin/exams/form/<int:exam_id>', methods=['GET','POST'])
def admin_exam_form(exam_id):
    if not admin_only():
        return redirect(url_for('login'))

    exam = None
    if exam_id:
        exam = Exam.query.get_or_404(exam_id)

    if request.method == 'POST':
        back = redirect(url_for('admin_exam_form', exam_id=exam_id))
        try:
            start = to_date(request.form.get('exam_start_date'))
            end = to_date(request.form.get('exam_end_date'))
            slot_deadline = to_date(request.form.get('slot_creation_deadline'))
            booking_deadline = to_date(request.form.get('booking_deadline'))
            max_marks = float(request.form.get('max_marks'))
            course_id = int(request.form.get('course_id'))
            examiner_id = request.form.get('examiner_id')
            if examiner_id:
                examiner_id = int(examiner_id)
            else:
                examiner_id = None
        except (ValueError, TypeError):
            flash("Please fill all fields correctly")
            return back

        if start is None or end is None or end < start:
            flash("End date cannot be before start date")
            return back

        if exam is None:
            exam = Exam()
            db.session.add(exam)
        exam.exam_name = request.form.get('exam_name')
        exam.exam_type = request.form.get('exam_type')
        exam.course_id = course_id
        exam.examiner_id = examiner_id
        exam.max_marks = max_marks
        exam.exam_start_date = start
        exam.exam_end_date = end
        exam.slot_creation_deadline = slot_deadline
        exam.booking_deadline = booking_deadline
        exam.slot_creation_open = request.form.get('slot_creation_open') == "on"
        exam.booking_open = request.form.get('booking_open') == "on"
        db.session.commit()
        flash("Exam saved")
        return redirect(url_for('admin_exams'))

    examiners = User.query.filter_by(role="staff", status="active").all()
    return render_template("admin/exam_form.html", exam=exam, courses=Course.query.all(), examiners=examiners)

@app.route('/admin/exams/delete/<int:exam_id>', methods=['POST'])
def admin_exam_delete(exam_id):
    if not admin_only():
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    if len(exam.slots) > 0:
        flash("Cannot delete: this exam already has slots")
    else:
        for r in exam.rubrics:
            db.session.delete(r)
        db.session.delete(exam)
        db.session.commit()
        flash("Exam deleted")
    return redirect(url_for('admin_exams'))


#                                                              ---------- Rubrics ----------
@app.route('/admin/rubrics')
def admin_rubrics():
    if not admin_only():
        return redirect(url_for('login'))

    return render_template("admin/rubrics.html", exams=Exam.query.all())

@app.route('/admin/rubrics/<int:exam_id>')
def admin_rubrics_exam(exam_id):
    if not admin_only():
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    total = 0
    for r in exam.rubrics:
        total = total + r.weightage
    return render_template("admin/rubrics_exam.html", exam=exam, total=total)


@app.route('/admin/rubrics/save/<int:rubric_id>', methods=['POST'])
def admin_rubric_save(rubric_id):
    if not admin_only():
        return redirect(url_for('login'))

    if rubric_id == 0:
        rubric = Rubric()
        exam = Exam.query.get_or_404(int(request.form.get('exam_id')))
    else:
        rubric = Rubric.query.get_or_404(rubric_id)
        exam = rubric.exam

    back = redirect(url_for('admin_rubrics_exam', exam_id=exam.exam_id))

    if request.form.get('do') == "delete":
        db.session.delete(rubric)
        db.session.commit()
        flash("Rubric deleted")
        return back

    try:
        weightage = float(request.form.get('weightage'))
    except (ValueError, TypeError):
        flash("Weightage must be a number")
        return back

    others = 0
    for r in exam.rubrics:
        if r != rubric:
            others = others + r.weightage

    if weightage <= 0 or others + weightage > 100:
        flash("Weightage must be above 0 and the total cannot go above 100")
        return back

    rubric.exam_id = exam.exam_id
    rubric.criterion_name = request.form.get('criterion_name')
    rubric.weightage = weightage
    rubric.description = request.form.get('description')
    if rubric_id == 0:
        db.session.add(rubric)
    db.session.commit()
    flash("Rubric saved")
    return back


#                                                                  ---------- Examiners ----------
@app.route('/admin/examiners')
def admin_examiners():
    if not admin_only():
        return redirect(url_for('login'))

    return render_template("admin/examiners.html", examiners=User.query.filter_by(role="staff").all())

@app.route('/admin/examiners/status/<int:user_id>', methods=['POST'])
def admin_examiner_status(user_id):
    if not admin_only():
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    new_status = request.form.get('status')
    if user.role != "staff" or new_status not in ["active", "inactive"]:
        flash("Wrong request")
    else:
        user.status = new_status
        db.session.commit()
        flash(user.name + " is now " + new_status)
    return redirect(url_for('admin_examiners'))

@app.route('/admin/examiners/add', methods=['GET','POST'])
def admin_examiner_form():
    if not admin_only():
        return redirect(url_for('login'))

    if request.method == 'POST':
        back = redirect(url_for('admin_examiner_form'))
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash("USER ALREADY EXIST")
            return back
        try:
            experience = int(request.form.get('experience'))
        except (ValueError, TypeError):
            flash("Experience must be a number")
            return back

       
        user = User(name=request.form.get('name'), email=email, password=request.form.get('password'),
                    role="staff", status="active", phone=request.form.get('phone'),
                    qualification=request.form.get('qualification'), experience=experience,
                    department=request.form.get('department'))
        db.session.add(user)
        db.session.commit()
        flash("Examiner added")
        return redirect(url_for('admin_examiners'))

    return render_template("admin/examiner_form.html")


#                                                 ---------- Slots----------
@app.route('/admin/slots')
def admin_slots():
    if not admin_only():
        return redirect(url_for('login'))

    exam_id = request.args.get('exam_id', type=int)
    if exam_id:
        slots = ExamSlot.query.filter_by(exam_id=exam_id).all()
    else:
        slots = ExamSlot.query.all()
    return render_template("admin/slots.html", slots=slots, exams=Exam.query.all(), exam_id=exam_id)


#                                                ---------- Bookings----------
@app.route('/admin/bookings')
def admin_bookings():
    if not admin_only():
        return redirect(url_for('login'))

    return render_template("admin/bookings.html", bookings=Booking.query.all())

@app.route('/admin/bookings/move/<int:booking_id>', methods=['POST'])
def admin_booking_move(booking_id):
    if not admin_only():
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)
    new_slot_id = request.form.get('slot_id', type=int)

    if new_slot_id is None or booking.status != "booked":
        flash("Nothing to move")
    else:
        new_slot = ExamSlot.query.get_or_404(new_slot_id)
        if new_slot.exam_id != booking.slot.exam_id:
            flash("Choose a slot of the same exam")
        elif new_slot.seats_left <= 0:
            flash("No seats left in that slot")
        else:
            booking.slot_id = new_slot.slot_id
            db.session.commit()
            flash("Booking rescheduled")
    return redirect(url_for('admin_bookings'))


#                                                       ---------- Students ----------
@app.route('/admin/students')
def admin_students():
    if not admin_only():
        return redirect(url_for('login'))

    return render_template("admin/students.html", students=User.query.filter_by(role="student").all())


#                                                           ---------- Search ----------
@app.route('/admin/search')
def admin_search():
    if not admin_only():
        return redirect(url_for('login'))

    search_type = request.args.get('type', 'student')
    q = request.args.get('q', '').strip()
    users = []
    exams = []
    bookings = []

    if q:
        if search_type in ["student", "staff"]:
            query = User.query.filter_by(role=search_type)
            if q.isdigit():
                users = query.filter(User.id == int(q)).all()
            else:
                users = query.filter(User.name.ilike("%" + q + "%")).all()
        elif search_type == "exam":
            if q.isdigit():
                exams = Exam.query.filter(Exam.exam_id == int(q)).all()
            else:
                exams = Exam.query.filter(Exam.exam_name.ilike("%" + q + "%")).all()
        elif search_type == "booking":
            if q.isdigit():
                bookings = Booking.query.filter(Booking.booking_id == int(q)).all()
            else:
                bookings = Booking.query.join(User, Booking.student_id == User.id).filter(User.name.ilike("%" + q + "%")).all()

    return render_template("admin/search.html", search_type=search_type, q=q,users=users, exams=exams, bookings=bookings)


#                                                                  --------------------------
#                                                                  <====EXAMINER PORTAL=====>
#                                                                  --------------------------

def staff_check():
    if staff_only():
        return None
    if session.get("role") == "staff":
        flash("Your account is waiting for admin approval")
        session.clear()
    return redirect(url_for('login'))

#                                                                ---------- Dashboard----------
@app.route('/staff_dashboard')
def staff_dashboard():
    blocked = staff_check()
    if blocked:
        return blocked

    me = session["user_id"]
    exams = Exam.query.filter_by(examiner_id=me).all()
    slots = []
    for e in exams:
        slots = slots + e.slots

    booked = 0
    pending = 0
    for s in slots:
        for b in s.bookings:
            if b.status == "booked":
                booked = booked + 1
                if b.marks is None:
                    pending = pending + 1

    stats = [("Assigned exams", len(exams)), ("Slots created", len(slots)),
             ("Students booked", booked), ("Pending evaluations", pending)]

    coming = [s for s in slots if s.date >= date.today()]
    coming.sort(key=lambda s: (s.date, s.start_time))
    return render_template("staff/dashboard.html", stats=stats, exams=exams, coming=coming[:5])

#                                                          ---------- Assigned exams ----------
@app.route('/staff/exams')
def staff_exams():
    blocked = staff_check()
    if blocked:
        return blocked

    return render_template("staff/exams.html", exams=Exam.query.filter_by(examiner_id=session["user_id"]).all())

#                                                            ---------- Slots----------
@app.route('/staff/slots')
def staff_slots():
    blocked = staff_check()
    if blocked:
        return blocked

    slots = []
    for e in Exam.query.filter_by(examiner_id=session["user_id"]).all():
        slots = slots + e.slots
    return render_template("staff/slots.html", slots=slots)

#                                                           ---------- Slot form----------
@app.route('/staff/slots/form', defaults={'slot_id': 0}, methods=['GET','POST'])
@app.route('/staff/slots/form/<int:slot_id>', methods=['GET','POST'])
def staff_slot_form(slot_id):
    blocked = staff_check()
    if blocked:
        return blocked

    me = session["user_id"]
    today = date.today()
    slot = None
    if slot_id:
        slot = ExamSlot.query.get_or_404(slot_id)
      
        if slot.exam.examiner_id != me:
            flash("This is not your slot")
            return redirect(url_for('staff_slots'))
        if slot.exam.booking_open or slot.booked > 0:
            flash("Student booking has started, you cannot change this slot")
            return redirect(url_for('staff_slots'))

    open_exams = []
    for e in Exam.query.filter_by(examiner_id=me).all():
        if e.slot_creation_open and (e.slot_creation_deadline is None or today <= e.slot_creation_deadline):
            open_exams.append(e)

    if request.method == 'POST':
        back = redirect(url_for('staff_slot_form', slot_id=slot_id))

        if slot:
            exam = slot.exam
        else:
            exam = Exam.query.get_or_404(int(request.form.get('exam_id')))
            if exam not in open_exams:
                flash("Slot creation is closed for this exam")
                return back

        try:
            slot_date = to_date(request.form.get('date'))
            start = to_time(request.form.get('start_time'))
            end = to_time(request.form.get('end_time'))
            seats = int(request.form.get('max_seats'))
        except (ValueError, TypeError):
            flash("Please fill all fields correctly")
            return back

        if slot_date is None or start is None or end is None:
            flash("Please fill all fields correctly")
            return back
        if slot_date < exam.exam_start_date or slot_date > exam.exam_end_date:
            flash("Slot date must be between the exam start and end date")
            return back
        if end <= start or seats <= 0:
            flash("End time must be after start time and seats must be more than 0")
            return back

        # same examiner cannot have two slots at the same time
        for s in ExamSlot.query.filter_by(date=slot_date).all():
            if s.exam.examiner_id == me and s.slot_id != slot_id and s.start_time < end and s.end_time > start:
                flash("You already have a slot at that time")
                return back

        if slot is None:
            slot = ExamSlot(exam_id=exam.exam_id)
            db.session.add(slot)
        slot.date = slot_date
        slot.start_time = start
        slot.end_time = end
        slot.max_seats = seats
        db.session.commit()
        flash("Slot saved")
        return redirect(url_for('staff_slots'))

    return render_template("staff/slot_form.html", slot=slot, open_exams=open_exams)

@app.route('/staff/slots/delete/<int:slot_id>', methods=['POST'])
def staff_slot_delete(slot_id):
    blocked = staff_check()
    if blocked:
        return blocked

    slot = ExamSlot.query.get_or_404(slot_id)
    if slot.exam.examiner_id != session["user_id"]:
        flash("This is not your slot")
    elif slot.exam.booking_open or slot.booked > 0:
        flash("Student booking has started, you cannot remove this slot")
    else:
        db.session.delete(slot)
        db.session.commit()
        flash("Slot removed")
    return redirect(url_for('staff_slots'))

#                                                 ---------- Students booked in a slot ----------
@app.route('/staff/slots/<int:slot_id>/students')
def staff_students(slot_id):
    blocked = staff_check()
    if blocked:
        return blocked

    slot = ExamSlot.query.get_or_404(slot_id)
    if slot.exam.examiner_id != session["user_id"]:
        flash("This is not your slot")
        return redirect(url_for('staff_slots'))

    students = [b for b in slot.bookings if b.status == "booked"]
    return render_template("staff/students.html", slot=slot, students=students)

#                                           ---------- Evaluate one student ----------
@app.route('/staff/evaluate/<int:booking_id>', methods=['GET','POST'])
def evaluate_student(booking_id):
    blocked = staff_check()
    if blocked:
        return blocked

    booking = Booking.query.get_or_404(booking_id)
    exam = booking.slot.exam

    if exam.examiner_id != session["user_id"] or booking.status != "booked":
        flash("You cannot evaluate this student")
        return redirect(url_for('staff_slots'))

    back = redirect(url_for('staff_students', slot_id=booking.slot_id))
    if len(exam.rubrics) == 0:
        flash("Admin has not added rubrics for this exam yet")
        return back

    if request.method == 'POST':
        scores = {}
        total_score = 0
        total_weight = 0
        for r in exam.rubrics:
            try:
                value = float(request.form.get("score_" + str(r.rubric_id)))
            except (ValueError, TypeError):
                flash("Enter a number for every rubric")
                return redirect(url_for('evaluate_student', booking_id=booking_id))
            if value < 0 or value > r.weightage:
                flash(r.criterion_name + " must be between 0 and " + str(r.weightage))
                return redirect(url_for('evaluate_student', booking_id=booking_id))
            scores[r.rubric_id] = value
            total_score = total_score + value
            total_weight = total_weight + r.weightage

        for old in booking.scores:
            db.session.delete(old)
        for rubric_id in scores:
            db.session.add(Score(booking_id=booking.booking_id, rubric_id=rubric_id, score=scores[rubric_id]))

        if total_weight <= 0:
            flash("The exam rubrics must have a positive total weightage")
            return redirect(url_for('evaluate_student', booking_id=booking_id))

        booking.marks = round(total_score / total_weight * exam.max_marks, 2)
        booking.remarks = request.form.get('remarks')
        db.session.commit()
        flash("Marks submitted")
        return back

    old_scores = {}
    for sc in booking.scores:
        old_scores[sc.rubric_id] = sc.score
    return render_template("staff/evaluate.html", booking=booking, exam=exam, old_scores=old_scores)

#                                                                   ---------- Profile ----------
@app.route('/staff/profile', methods=['GET','POST'])
def staff_profile():
    blocked = staff_check()
    if blocked:
        return blocked

    user = db.session.get(User, session["user_id"])

    if request.method == 'POST':
        try:
            user.experience = int(request.form.get('experience'))
        except (ValueError, TypeError):
            flash("Experience must be a number")
            return redirect(url_for('staff_profile'))

        user.name = request.form.get('name')
        if request.form.get('password'):
            user.password = request.form.get('password')
        user.phone = request.form.get('phone')
        user.qualification = request.form.get('qualification')
        user.department = request.form.get('department')
        db.session.commit()
        session["name"] = user.name
        flash("Profile updated")
        return redirect(url_for('staff_profile'))

    return render_template("staff/profile.html", user=user)


#                                                                  --------------------------
#                                                                  <====STUDENT PORTAL=====>
#                                                                  --------------------------

def booking_sort_key(b):
    return (b.slot.date, b.slot.start_time)

#                                                             ---------- Dashboard ----------
@app.route('/student_dashboard')
def student_dashboard():
    if not student_only():
        return redirect(url_for('login'))

    today = date.today()
    bookings = Booking.query.filter_by(student_id=session["user_id"]).all()
    upcoming = [b for b in bookings if b.status == "booked" and b.slot.date >= today]
    upcoming.sort(key=booking_sort_key)
    results = [b for b in bookings if b.marks is not None]
    cancelled = [b for b in bookings if b.status == "cancelled"]

    stats = [("Upcoming exams", len(upcoming)), ("Total bookings", len(bookings)),
             ("Cancelled", len(cancelled)), ("Results published", len(results))]
    return render_template("student/dashboard.html", stats=stats, upcoming=upcoming)

#                                                              ---------- Exams: search ----------
@app.route('/student/exams')
def student_exams():
    if not student_only():
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip()
    exam_type = request.args.get('exam_type', '')
    course_id = request.args.get('course_id', '')

  
    if course_id and not course_id.isdigit():
        course_id = ""

    query = Exam.query.join(Course).filter(Course.status == "active")
    if q:
        query = query.filter(or_(Exam.exam_name.ilike("%" + q + "%"), Course.course_name.ilike("%" + q + "%")))
    if exam_type:
        query = query.filter(Exam.exam_type == exam_type)
    if course_id:
        query = query.filter(Exam.course_id == int(course_id))

    courses = Course.query.filter_by(status="active").all()
    types = [t[0] for t in db.session.query(Exam.exam_type).distinct().all()]
    return render_template("student/exams.html", exams=query.all(), courses=courses, types=types,
                           q=q, exam_type=exam_type, course_id=course_id)


@app.route('/student/exams/<int:exam_id>/slots')
def student_slots(exam_id):
    if not student_only():
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    already_booked = False
    for b in Booking.query.filter_by(student_id=session["user_id"], status="booked").all():
        if b.slot.exam_id == exam_id:
            already_booked = True
    return render_template("student/slots.html", exam=exam, already_booked=already_booked)

@app.route('/student/book/<int:slot_id>', methods=['POST'])
def book_slot(slot_id):
    if not student_only():
        return redirect(url_for('login'))

    slot = ExamSlot.query.get_or_404(slot_id)
    exam = slot.exam
    me = session["user_id"]
    back = redirect(url_for('student_slots', exam_id=exam.exam_id))

    if not exam.booking_open:
        flash("Booking is closed for this exam")
        return back
    if exam.booking_deadline and date.today() > exam.booking_deadline:
        flash("Booking deadline is over")
        return back
    if slot.seats_left <= 0:
        flash("This slot is full")
        return back

    # no double booking for the same exam
    for b in Booking.query.filter_by(student_id=me, status="booked").all():
        if b.slot.exam_id == exam.exam_id:
            flash("You have already booked this exam")
            return back

    db.session.add(Booking(student_id=me, slot_id=slot.slot_id, booking_date=date.today(), status="booked"))
    db.session.commit()
    flash("Slot booked")
    return redirect(url_for('student_bookings'))

#                                                           ---------- My bookings  ----------
@app.route('/student/bookings')
def student_bookings():
    if not student_only():
        return redirect(url_for('login'))

    today = date.today()
    bookings = Booking.query.filter_by(student_id=session["user_id"]).all()
    upcoming = [b for b in bookings if b.status == "booked" and b.slot.date >= today]
    upcoming.sort(key=booking_sort_key)
    history = [b for b in bookings if b not in upcoming]
    history.sort(key=booking_sort_key, reverse=True)
    return render_template("student/bookings.html", upcoming=upcoming, history=history, today=today)

@app.route('/student/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if not student_only():
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)
    deadline = booking.slot.exam.booking_deadline

    if booking.student_id != session["user_id"] or booking.status != "booked":
        flash("You cannot cancel this booking")
    elif deadline and date.today() > deadline:
        flash("Booking deadline is over, you cannot cancel now")
    elif booking.marks is not None:
        flash("This exam is already evaluated")
    else:
        booking.status = "cancelled"
        db.session.commit()
        flash("Booking cancelled")
    return redirect(url_for('student_bookings'))

#                                                                          ---------- Results + feedback ----------
@app.route('/student/results')
def student_results():
    if not student_only():
        return redirect(url_for('login'))

    bookings = Booking.query.filter_by(student_id=session["user_id"]).all()
    results = [b for b in bookings if b.marks is not None]
    results.sort(key=booking_sort_key, reverse=True)
    return render_template("student/results.html", results=results)

#                                                                       ---------- Profile ----------
@app.route('/student/profile', methods=['GET','POST'])
def student_profile():
    if not student_only():
        return redirect(url_for('login'))

    user = db.session.get(User, session["user_id"])

    if request.method == 'POST':
        user.name = request.form.get('name')
        if request.form.get('password'):
            user.password = request.form.get('password')
        db.session.commit()
        session["name"] = user.name
        flash("Profile updated")
        return redirect(url_for('student_profile'))

    return render_template("student/profile.html", user=user)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))





































if __name__ == "__main__":
    app.run(debug=True)
