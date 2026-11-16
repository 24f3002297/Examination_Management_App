from extensions import db


class User(db.Model):
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)          
    status = db.Column(db.String(20), default="pending")    

    # extra details, only used by examiners
    phone = db.Column(db.String(15))
    qualification = db.Column(db.String(100))
    experience = db.Column(db.Integer)
    department = db.Column(db.String(100))



class Course(db.Model):
    __tablename__ = "course_list"

    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(100), nullable=False)       

    exams = db.relationship("Exam", backref="course")



class Exam(db.Model):
    __tablename__ = "exam"

    exam_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course_list.course_id"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("User.id"))     
    exam_name = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(db.String(100), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    exam_start_date = db.Column(db.Date, nullable=False)
    exam_end_date = db.Column(db.Date, nullable=False)

    # timeline + open/close switches (set by admin)
    slot_creation_deadline = db.Column(db.Date)
    booking_deadline = db.Column(db.Date)
    slot_creation_open = db.Column(db.Boolean, default=False)
    booking_open = db.Column(db.Boolean, default=False)

    examiner = db.relationship("User")
    rubrics = db.relationship("Rubric", backref="exam")
    slots = db.relationship("ExamSlot", backref="exam")



class Rubric(db.Model):
    __tablename__ = "examination_rubric"

    rubric_id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.exam_id"), nullable=False)
    criterion_name = db.Column(db.String(50), nullable=False)
    weightage = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)



class ExamSlot(db.Model):
    __tablename__ = "exam_slot"

    slot_id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.exam_id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_seats = db.Column(db.Integer, nullable=False)

    bookings = db.relationship("Booking", backref="slot")

   
    @property
    def booked(self):
        count = 0
        for b in self.bookings:
            if b.status == "booked":
                count = count + 1
        return count

    @property
    def seats_left(self):
        return self.max_seats - self.booked

    @property
    def time_text(self):
        return self.start_time.strftime("%H:%M") + " - " + self.end_time.strftime("%H:%M")



class Booking(db.Model):
    __tablename__ = "bookings"

    booking_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("exam_slot.slot_id"), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), nullable=False)        

    marks = db.Column(db.Float)                              
    remarks = db.Column(db.String(300))

    student = db.relationship("User")
    scores = db.relationship("Score", backref="booking")



class Score(db.Model):
    __tablename__ = "score"

    score_id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.booking_id"), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey("examination_rubric.rubric_id"), nullable=False)
    score = db.Column(db.Float, nullable=False)

    rubric = db.relationship("Rubric")