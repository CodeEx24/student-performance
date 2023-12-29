from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from flask_login import UserMixin
import os

db = SQLAlchemy()


class Student(db.Model, UserMixin):
    __tablename__ = 'Students'

    StudentId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    StudentNumber = db.Column(db.String(30), unique=True, nullable=False)  # UserID
    Name = db.Column(db.String(50), nullable=False)  # Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(128), nullable=False)  # Password
    Gender = db.Column(db.Integer, nullable=True)  # Gender
    DateOfBirth = db.Column(db.Date)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    # Dropout = db.Column(db.Boolean)  # Dropout
    # IsGraduated = db.Column(db.Boolean, default=True)
    Token = db.Column(db.String(128))  # This field will store the reset token
    TokenExpiration = db.Column(db.DateTime)
    # IsBridging
    
    def to_dict(self):
        return {
            'StudentId': self.StudentId,
            'StudentNumber': self.StudentNumber,
            'Name': self.Name,
            'Email': self.Email,
            'Password': self.Password,
            'Gender': self.Gender,
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'Dropout': self.Dropout,
            'IsGraduated': self.IsGraduated
        }

    def get_id(self):
        return str(self.StudentId)  # Convert to string to ensure compatibility


class Faculty(db.Model, UserMixin):
    __tablename__ = 'Faculties'

    TeacherId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TeacherNumber = db.Column(db.String(30), unique=True)  # UserID
    Name = db.Column(db.String(50), nullable=False)  # Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(128), nullable=False)  # Password
    Gender = db.Column(db.Integer)  # Gender
    DateOfBirth = db.Column(db.Date)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    IsActive = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'TeacherId': self.TeacherId,
            'TeacherNumber': self.TeacherNumber,
            'Name': self.Name,
            'Email': self.Email,
            'Password': self.Password,
            'Gender': self.Gender,
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsActive': self.IsActive
        }

    def get_id(self):
        return str(self.TeacherId)  # Convert to string to ensure compatibility


class UniversityAdmin(db.Model, UserMixin):
    __tablename__ = 'UniversityAdmins'

    UnivAdminId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UnivAdminNumber = db.Column(db.String(30), unique=True)  # UserID
    Name = db.Column(db.String(50), nullable=False)  # Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(128), nullable=False)  # Password
    Gender = db.Column(db.Integer)  # Gender
    DateOfBirth = db.Column(db.Date)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    IsActive = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'UnivAdminId': self.UnivAdminId,
            'UnivAdminNumber': self.UnivAdminNumber,
            'Name': self.Name,
            'Email': self.Email,
            'Password': self.Password,
            'Gender': self.Gender,
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsActive': self.IsActive
        }

    def get_id(self):
        # Convert to string to ensure compatibility
        return str(self.UnivAdminId)


class SystemAdmin(db.Model, UserMixin):
    __tablename__ = 'SystemAdmins'

    SysAdminId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SysAdminNumber = db.Column(db.String(30), unique=True)  # UserID
    Name = db.Column(db.String(50), nullable=False)  # Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(128), nullable=False)  # Password
    Gender = db.Column(db.Integer)  # Gender
    DateOfBirth = db.Column(db.Date)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    IsActive = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'SysAdminId': self.SysAdminId,
            'SysAdminNumber': self.SysAdminNumber,
            'Name': self.Name,
            'Email': self.Email,
            'Password': self.Password,
            'Gender': self.Gender,
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsActive': self.IsActive
        }

    def get_id(self):
        # Convert to string to ensure compatibility
        return str(self.SysAdminId)


class Course(db.Model):
    __tablename__ = 'Course'

    CourseId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CourseCode = db.Column(db.String(10), unique=True)
    Name = db.Column(db.String(200))
    Description = db.Column(db.String(200))

    def to_dict(self):
        return {
            'CourseId': self.CourseId,
            'CourseCode': self.CourseCode,
            'Name': self.Name,
            'Description': self.Description
        }


class CourseEnrolled(db.Model):
    __tablename__ = 'CourseEnrolled'

    CourseId = db.Column(db.Integer, db.ForeignKey(
        'Course.CourseId', ondelete="CASCADE"), primary_key=True)
    StudentId = db.Column(db.Integer, db.ForeignKey(
        'Students.StudentId', ondelete="CASCADE"), primary_key=True)
    DateEnrolled = db.Column(db.Date)
    Status = db.Column(db.Integer, nullable=False) 
    # 0 - Not Graduated ||  1 - Graduated  ||  2 - Drop  ||  3 - Transfer Course || 4 - Transfer School
    CurriculumYear = db.Column(db.Integer, nullable=False)  


    def to_dict(self):
        return {
            'CourseId': self.CourseId,
            'StudentId': self.StudentId,
            'DateEnrolled': self.DateEnrolled
        }

class Metadata(db.Model):
    __tablename__ = 'Metadata'

    MetadataId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CourseId = db.Column(db.Integer, db.ForeignKey('Course.CourseId', ondelete="CASCADE"))
    Year = db.Column(db.Integer, nullable=False) # Change this
    Semester = db.Column(db.Integer, nullable=False)
    Batch = db.Column(db.Integer, nullable=False)


class Class(db.Model):
    __tablename__ = 'Class'

    ClassId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Section = db.Column(db.Integer)
    IsGradeFinalized = db.Column(db.Boolean, default=False)
    MetadataId = db.Column(db.Integer, db.ForeignKey(
        'Metadata.MetadataId', ondelete="CASCADE"))
    
    __table_args__ = (db.UniqueConstraint('MetadataId', 'Section', name='uq_metadata_section'),)

    def to_dict(self):
        return {
            'ClassId': self.ClassId,
            'Section': self.Section,
            'IsGradeFinalized': self.IsGradeFinalized,
            'MetadataId': self.MetadataId
        }
    
    # Adding a unique constraint
   

class Subject(db.Model):
    __tablename__ = 'Subject'

    SubjectId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SubjectCode = db.Column(db.String(20), unique=True)
    Name = db.Column(db.String(200))
    Description = db.Column(db.String(200))
    Units = db.Column(db.Float)
    IsNSTP = db.Column(db.Boolean, default=False)
    # ForBridging

    def to_dict(self):
        return {
            'SubjectId': self.SubjectId,
            'SubjectCode': self.SubjectCode,
            'Name': self.Name,
            'Description': self.Description,
            'Units': self.Units,
            'IsNSTP': self.IsNSTP,
        }


class ClassSubject(db.Model):
    __tablename__ = 'ClassSubject'

    ClassSubjectId = db.Column(
        db.Integer, primary_key=True, autoincrement=True)
    ClassId = db.Column(db.Integer, db.ForeignKey(
        'Class.ClassId', ondelete="CASCADE"))
    SubjectId = db.Column(db.Integer, db.ForeignKey(
        'Subject.SubjectId', ondelete="CASCADE"))
    TeacherId = db.Column(db.Integer, db.ForeignKey(
        'Faculties.TeacherId', ondelete="CASCADE"), nullable=True)
    Schedule = db.Column(db.String(100), nullable=True)

    # Adding a unique constraint on the combination of ClassId, SubjectId, and TeacherId
    __table_args__ = (db.UniqueConstraint(
        'ClassId', 'SubjectId', 'TeacherId', name='_unique_class_subject_teacher'),)

    def to_dict(self):
        return {
            'ClassSubjectId': self.ClassSubjectId,
            'ClassId': self.ClassId,
            'SubjectId': self.SubjectId,
            'TeacherId': self.TeacherId,
            'Schedule': self.Schedule,
        }


class StudentClassSubjectGrade(db.Model):
    __tablename__ = 'StudentClassSubjectGrade'

    # StudentClassSubjectGradeId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ClassSubjectId = db.Column(db.Integer, db.ForeignKey(
        'ClassSubject.ClassSubjectId', ondelete="CASCADE"), primary_key=True)
    StudentId = db.Column(db.Integer, db.ForeignKey(
        'Students.StudentId', ondelete="CASCADE"), primary_key=True)
    # Grade = db.Column(db.String(5), CheckConstraint("Grade IN ('INC', 'W', '1.00', '1.25', '1.5', '1.75', '2.00', '2.25', '2.5', '2.75', '3.0', '4.0', '5.0')"))
    Grade = db.Column(db.Float)
    DateEnrolled = db.Column(db.Date)
    AcademicStatus = db.Column(db.Integer) # Status 1 = Passed (3.0) , 2 (4.0, 5.0)= Failed, 3 //////////  Incomplete = (INC),  Withdrawn = (W)

    def to_dict(self):
        return {
            'ClassSubjectId': self.ClassSubjectId,
            'StudentId': self.StudentId,
            'Grade': self.Grade,
            'DateEnrolled': self.DateEnrolled,
            'AcademicStatus': self.AcademicStatus,
        }


class StudentClassGrade(db.Model):
    __tablename__ = 'StudentClassGrade'
    
    # StudentClassGradeId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    StudentId = db.Column(db.Integer, db.ForeignKey(
        'Students.StudentId', ondelete="CASCADE"), primary_key=True)
    ClassId = db.Column(db.Integer, db.ForeignKey(
        'Class.ClassId', ondelete="CASCADE"), primary_key=True)
    Grade = db.Column(db.Float)
    Lister = db.Column(db.Integer) # 1 - President, 2 - Dean, 0 - Not Lister

    def to_dict(self):
        return {
            'StudentId': self.StudentId,
            'ClassId': self.ClassId,
            'Grade': self.Grade,
            'IsLister': self.IsLister
        }


class ClassSubjectGrade(db.Model):
    __tablename__ = 'ClassSubjectGrade'

    ClassSubjectGradeId = db.Column(
        db.Integer, primary_key=True, autoincrement=True)
    ClassSubjectId = db.Column(db.Integer, db.ForeignKey(
        'ClassSubject.ClassSubjectId', ondelete="CASCADE"), unique=True)
    Grade = db.Column(db.Float)
    Passed = db.Column(db.Integer)
    Failed = db.Column(db.Integer)
    Incomplete = db.Column(db.Integer)
    Dropout = db.Column(db.Integer)

    def to_dict(self):
        return {
            'ClassSubjectGradeId': self.ClassSubjectGradeId,
            'ClassSubjectId': self.ClassSubjectId,
            'Grade': self.Grade,
            'Passed': self.Passed,
            'Failed': self.Failed,
            'Incomplete': self.Incomplete,
            'Dropout': self.Dropout
        }


class ClassGrade(db.Model):
    __tablename__ = 'ClassGrade'

    ClassGradeId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ClassId = db.Column(db.Integer, db.ForeignKey(
        'Class.ClassId', ondelete="CASCADE"), unique=True)
    DeansLister = db.Column(db.Integer)
    PresidentsLister = db.Column(db.Integer)
    Grade = db.Column(db.Float)

    def to_dict(self):
        return {
            'ClassGradeId': self.ClassGradeId,
            'ClassId': self.ClassId,
            'DeanLister': self.DeanLister,
            'PresidentLister': self.PresidentLister,
            'Grade': self.Grade
        }


class CourseGrade(db.Model):
    __tablename__ = 'CourseGrade'

    CourseGradeId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CourseId = db.Column(db.Integer, db.ForeignKey(
        'Course.CourseId', ondelete="CASCADE"))
    Batch = db.Column(db.Integer, primary_key=True)
    Semester = db.Column(db.Integer, primary_key=True, nullable=False)
    Grade = db.Column(db.Float)

    def to_dict(self):
        return {
            'CourseGradeId': self.CourseGradeId,
            'CourseId': self.CourseId,
            'Year': self.Year,
            'Grade': self.Grade,
        }


class Curriculum(db.Model):
    __tablename__ = 'Curriculum'

    CurriculumId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SubjectId = db.Column(db.Integer, db.ForeignKey('Subject.SubjectId', ondelete="CASCADE"))
    MetadataId = db.Column(db.Integer, db.ForeignKey('Metadata.MetadataId', ondelete="CASCADE"), nullable=False)

    def to_dict(self):
        return {
            'CurriculumId': self.CurriculumId,
            'SubjectId': self.SubjectId,
            'MetadataId': self.MetadataId
            # Add other attributes if needed
        }

        
config_mode = os.getenv("CONFIG_MODE")
add_data = os.getenv("ADD_DATA")

print('/'+config_mode+'/')
print('/'+add_data+'/')

def init_db(app):
    db.init_app(app)
    
    if add_data=='True':
        print("Adding data")
        from data.data2.student import student_data
        from data.data2.faculty import faculty_data
        from data.data2.universityadmin import university_admin_data
        from data.data2.systemadmin import system_admin_data
        from data.data2.course import course_data
        from data.data2.courseEnrolled import course_enrolled_data
        from data.data2.subject import subject_data
        from data.data2.classes import class_data
        from data.data2.classSubject import class_subject_data
        from data.data2.studentClassSubjectGrade import student_class_subject_grade_data
        from data.data2.studentClassGrade import student_class_grade_data
        from data.data2.classSubjectGrade import class_subject_grade_data
        from data.data2.classGrade import class_grade_data
        from data.data2.courseGrade import course_grade_data
        from data.data2.curriculum import curriculum_data
        from data.data2.metadata import metadata_data

        def create_sample_data():
            for data in student_data:
                student = Student(**data)
                db.session.add(student)

            for data in faculty_data:
                faculty = Faculty(**data)
                db.session.add(faculty)

            for data in university_admin_data:
                university_admin = UniversityAdmin(**data)
                db.session.add(university_admin)

            for data in system_admin_data:
                system_admin = SystemAdmin(**data)
                db.session.add(system_admin)

            for data in course_data:
                course = Course(**data)
                db.session.add(course)
                db.session.flush()
                
            for data in subject_data:
                subject = Subject(**data)
                db.session.add(subject)
                db.session.flush()

            for data in metadata_data:
                metadata = Metadata(**data)
                db.session.add(metadata)
                db.session.flush()

            for data in curriculum_data:
                curriculum = Curriculum(**data)
                db.session.add(curriculum)
                db.session.flush()
                
            for data in course_enrolled_data:
                course_enrolled = CourseEnrolled(**data)
                db.session.add(course_enrolled)
                db.session.flush()

            
            for data in class_data:
                class_ = Class(**data)
                db.session.add(class_)
                db.session.flush()

            for data in class_subject_data:
                class_subject = ClassSubject(**data)
                db.session.add(class_subject)
                db.session.flush()

            for data in student_class_subject_grade_data:
                student_class_subject_grade = StudentClassSubjectGrade(**data)
                db.session.add(student_class_subject_grade)
                db.session.flush()

            for data in student_class_grade_data:
                student_class_grade = StudentClassGrade(**data)
                db.session.add(student_class_grade)
                db.session.flush()

            for data in class_subject_grade_data:
                class_subject_grade = ClassSubjectGrade(**data)
                db.session.add(class_subject_grade)
                db.session.flush()

            for data in class_grade_data:
                class_grade = ClassGrade(**data)
                db.session.add(class_grade)
                db.session.flush()

            for data in course_grade_data:
                course_grade = CourseGrade(**data)
                db.session.add(course_grade)
                db.session.flush()
            
            db.session.commit()
            db.session.close()

    
    if config_mode == 'development' :
        with app.app_context():
            inspector = inspect(db.engine)
            db.create_all()
            
            if add_data=='True' and 'Students' not in inspector.get_table_names():
                print("DEVELOPMENT AND ADDING DATA")
                create_sample_data()

  