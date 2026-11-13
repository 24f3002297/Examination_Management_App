from extensions import db

class User(db.Model):
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)


class Course(db.Model):
    __tablename__ = "course_list"

    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(100), nullable=False)

    exams = db.relationship("Exam", back_populates="course")


class Exam(db.Model):
    __tablename__ = "exam"

    exam_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer,db.ForeignKey("course_list.course_id"),nullable=False)
    exam_name = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(db.String(100), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    exam_start_date = db.Column(db.Date, nullable=False)
    exam_end_date = db.Column(db.Date, nullable=False)

    course = db.relationship("Course", back_populates="exams")
    rubrics = db.relationship("ExaminationRubric", back_populates="exam")
    slots = db.relationship("ExamSlot", back_populates="exam")


class ExaminationRubric(db.Model):
    __tablename__ = "examination_rubric"

    rubric_id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer,db.ForeignKey("exam.exam_id"),nullable=False)
    criterion_name = db.Column(db.String(50), nullable=False)
    weightage = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)

    exam = db.relationship("Exam", back_populates="rubrics")


class ExamSlot(db.Model):
    __tablename__ = "exam_slot"

    slot_id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer,db.ForeignKey("exam.exam_id"),nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_seats = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False)

    exam = db.relationship("Exam", back_populates="slots")

class Booking(db.Model):
    __tablename__ = "bookings"

    booking_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("exam_slot.slot_id"), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), nullable=False)

    student = db.relationship("User")
    slot = db.relationship("ExamSlot")


class ExaminerProfile(db.Model):
    __tablename__ = "examiner_profile"

    profile_id = db.Column(db.Integer, primary_key=True)
    examiner_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, unique=True)
    phone = db.Column(db.String(15), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(100), nullable=False)

    examiner = db.relationship("User")
