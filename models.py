from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
import os

import time
from datetime import datetime
from sqlalchemy import text

from flask_sqlalchemy import SQLAlchemy

from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)

db = SQLAlchemy()

# Student Users
class Student(db.Model): # (class SPSStudent) In DJANGO you must set the name directly here 
    __tablename__ = 'SPSStudent' # Set the name of table in database (Available for FLASK framework)

    StudentId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    StudentNumber = db.Column(db.String(30), unique=True, nullable=False)  # UserID
    FirstName = db.Column(db.String(50), nullable=False)  # First Name
    LastName = db.Column(db.String(50), nullable=False)  # Last Name
    MiddleName = db.Column(db.String(50))  # Middle Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(256), nullable=False)  # Password
    Gender = db.Column(db.Integer, nullable=True)  # Gender
    DateOfBirth = db.Column(db.Date)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    IsOfficer = db.Column(db.Boolean, default=False)
    Token = db.Column(db.String(128))  # This is for handling reset password 
    TokenExpiration = db.Column(db.DateTime) # This is for handling reset password 
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    # IsBridging
    
    def to_dict(self):
        full_name = self.LastName + ', ' + self.FirstName + ' ' + self.MiddleName
        return {
            'StudentId': self.StudentId,
            'StudentNumber': self.StudentNumber,
            'Name': full_name,
            'Email': self.Email,
            'Gender': "Male" if self.Gender == 1 else "Female",
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsOfficer': self.IsOfficer
        }

    def get_id(self):
        return str(self.StudentId)  # Convert to string to ensure compatibility

    def get_user_id(self):
        return self.StudentId

# Faculty Users
class Faculty(db.Model):
    __tablename__ = 'FISFaculty' # Set the name of table in database
    FacultyId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FacultyType = db.Column(db.String(50), nullable=False)  # Faculty Type
    Rank = db.Column(db.String(50))  # Faculty Rank
    Units = db.Column(db.Numeric, nullable=False)  # Faculty Unit
    FirstName = db.Column(db.String(50), nullable=False)  # First Name
    LastName = db.Column(db.String(50), nullable=False)  # Last Name
    MiddleName = db.Column(db.String(50))  # Middle Name
    MiddleInitial = db.Column(db.String(50))  # Middle Initial
    NameExtension = db.Column(db.String(50))  # Name Extension
    BirthDate = db.Column(db.Date, nullable=False)  # Birthdate
    DateHired = db.Column(db.Date, nullable=False)  # Date Hired
    Degree = db.Column(db.String)  # Degree
    Remarks = db.Column(db.String)  # Remarks
    FacultyCode = db.Column(db.Integer, nullable=False)  # Faculty Code
    Honorific = db.Column(db.String(50))  # Honorific
    Age = db.Column(db.Numeric, nullable=False)  # Age
    
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    Gender = db.Column(db.Integer) # Gender # 1 if Male 2 if Female
    
    Password = db.Column(db.String(256), nullable=False)  # Password
    ProfilePic= db.Column(db.String(50),default="14wkc8rPgd8NcrqFoRFO_CNyrJ7nhmU08")  # Profile Pic
    IsActive = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    # FOREIGN TABLES
    

    def to_dict(self):
        full_name = self.LastName + ', ' + self.FirstName + ' ' + self.MiddleName
        return {
            'FacultyId': self.FacultyId,
            'FacultyType': self.FacultyType,
            'Name': full_name,
            'Email': self.Email,
            'Gender': "Male" if self.Gender == 1 else "Female",
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
        }
        
    def get_id(self):
        return str(self.faculty_account_id)  # Convert to string to ensure compatibility

# University Admin Users
class UniversityAdmin(db.Model):
    __tablename__ = 'SPSUniversityAdmin'

    UnivAdminId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UnivAdminNumber = db.Column(db.String(30), unique=True)  # UserID
    FirstName = db.Column(db.String(50), nullable=False)  # First Name
    LastName = db.Column(db.String(50), nullable=False)  # Last Name
    MiddleName = db.Column(db.String(50))  # Middle Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(256), nullable=False)  # Password
    Gender = db.Column(db.Integer)  # Gender
    DateOfBirth = db.Column(db.Date)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    IsActive = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        full_name = self.LastName + ', ' + self.FirstName + ' ' + self.MiddleName
        return {
            'UnivAdminId': self.UnivAdminId,
            'UnivAdminNumber': self.UnivAdminNumber,
            'Name': full_name,
            'Email': self.Email,
            'Gender': "Male" if self.Gender == 1 else "Female",
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsActive': self.IsActive
        }

    def get_id(self):
        # Convert to string to ensure compatibility
        return str(self.UnivAdminId)
    
# University Admin Users
class Registrar(db.Model):
    __tablename__ = 'SPSRegistrar'

    RegistrarId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    RegistrarNumber = db.Column(db.String(30), unique=True)  # UserID
    FirstName = db.Column(db.String(50), nullable=False)  # First Name
    LastName = db.Column(db.String(50), nullable=False)  # Last Name
    MiddleName = db.Column(db.String(50))  # Middle Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(256), nullable=False)  # Password
    Gender = db.Column(db.Integer)  # Gender
    DateOfBirth = db.Column(db.Date)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    IsActive = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        full_name = self.LastName + ', ' + self.FirstName + ' ' + self.MiddleName
        return {
            'RegistrarId': self.RegistrarId,
            'RegistrarNumber': self.RegistrarNumber,
            'Name': full_name,
            'Email': self.Email,
            'Gender': "Male" if self.Gender == 1 else "Female",
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsActive': self.IsActive
        }

    def get_id(self):
        # Convert to string to ensure compatibility
        return str(self.UnivAdminId)
    
# University Admin Users
class StudentRequirements(db.Model):
    __tablename__ = 'SPSStudentRequirements'

    StudentId = db.Column(db.Integer, db.ForeignKey('SPSStudent.StudentId', ondelete="CASCADE"), primary_key=True) # Students Reference
    F_137 = db.Column(db.Boolean, default=False)
    F_138 = db.Column(db.Boolean, default=False)
    GoodMoralSeal    = db.Column(db.Boolean, default=False)
    Grade12 = db.Column(db.Boolean, default=False)
    Grade11 = db.Column(db.Boolean, default=False)
    SARForm = db.Column(db.Boolean, default=False)
    PSA = db.Column(db.Boolean, default=False)
    Diploma = db.Column(db.Boolean, default=False)
    Grade10WithoutSeal = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'F_137': self.F_137,
            'F_138': self.F_138,
            'GoodMoralSeal': self.GoodMoralSeal,
            'Grade12': self.Grade12,
            'Grade11': self.Grade11,
            'SARForm': self.SARForm,
            'PSA': self.PSA,
            'Diploma': self.Diploma,
            'Grade10WithoutSeal': self.Grade10WithoutSeal
        }
        
# System Admins Users
class SystemAdmin(db.Model):
    __tablename__ = 'SPSSystemAdmin'

    SysAdminId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SysAdminNumber = db.Column(db.String(30), unique=True)  # UserID
    FirstName = db.Column(db.String(50), nullable=False)  # First Name
    LastName = db.Column(db.String(50), nullable=False)  # Last Name
    MiddleName = db.Column(db.String(50))  # Middle Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(256), nullable=False)  # Password
    Gender = db.Column(db.Integer)  # Gender
    DateOfBirth = db.Column(db.Date)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    IsActive = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        full_name = f"{self.LastName} {self.FirstName} {self.MiddleName}" if self.MiddleName else f"{self.LastName} {self.FirstName}"
        
        return {
            'SysAdminId': self.SysAdminId,
            'SysAdminNumber': self.SysAdminNumber,
            'Name': full_name,
            'Email': self.Email,
            'Gender': "Male" if self.Gender == 1 else "Female",
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsActive': self.IsActive
        }

    def get_user_id(self):
        return self.SysAdminId
   
# Course List
class Course(db.Model):
    __tablename__ = 'SPSCourse'

    CourseId = db.Column(db.Integer, primary_key=True, autoincrement=True) # Unique Identifier
    CourseCode = db.Column(db.String(10), unique=True) # Course Code - (BSIT, BSHM, BSCS)
    Name = db.Column(db.String(200)) # (Name of Course (Bachelor of Science in Information Technology)
    Description = db.Column(db.String(200)) # Description of course
    IsValidPUPQCCourses = db.Column(db.Boolean, default=True) # APMS are handling different courses so there are specific courses available in QC Only
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'CourseId': self.CourseId,
            'CourseCode': self.CourseCode,
            'Name': self.Name,
            'Description': self.Description,
            'IsValidPUPQCCourses': self.IsValidPUPQCCourses
        }

# Student Enrolled in the courses
class CourseEnrolled(db.Model):
    __tablename__ = 'SPSCourseEnrolled'

    CourseId = db.Column(db.Integer, db.ForeignKey('SPSCourse.CourseId', ondelete="CASCADE"), primary_key=True)  # Unique Identifier
    StudentId = db.Column(db.Integer, db.ForeignKey('SPSStudent.StudentId', ondelete="CASCADE"), primary_key=True) # Students Reference
    DateEnrolled = db.Column(db.Date) # Date they enrolled
    Status = db.Column(db.Integer, nullable=False)  # (0 - Not Graduated/Continuing ||  1 - Graduated  ||  2 - Drop  ||  3 - Transfer Course || 4 - Transfer School)
    CurriculumYear = db.Column(db.Integer, nullable=False)  # (2019, 2020, 2021) - For checking what the subjects they should taken
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


    def to_dict(self):
        return {
            'CourseId': self.CourseId,
            'StudentId': self.StudentId,
            'DateEnrolled': self.DateEnrolled,
        }

# Metadata containing the details of class such as Year, Semester, Batch and Course
class Metadata(db.Model):
    __tablename__ = 'SPSMetadata'

    MetadataId = db.Column(db.Integer, primary_key=True, autoincrement=True) # Unique Identifier
    CourseId = db.Column(db.Integer, db.ForeignKey('SPSCourse.CourseId', ondelete="CASCADE")) # Course References
    Year = db.Column(db.Integer, nullable=False) # (1, 2, 3, 4) - Current year of the class 
    Semester = db.Column(db.Integer, nullable=False) # (1, 2, 3) - Current semester of class
    Batch = db.Column(db.Integer, nullable=False) # (2019, 2020, 2021, ...) - Batch of the class
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# Class Details 
class Class(db.Model):
    __tablename__ = 'SPSClass'

    ClassId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MetadataId = db.Column(db.Integer, db.ForeignKey('SPSMetadata.MetadataId', ondelete="CASCADE")) # Metadata containing details of class year, semester, batch, course
    Section = db.Column(db.Integer) # Section of the class
    IsGradeFinalized = db.Column(db.Boolean, default=False) # Checker if the grade is Finalized
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (db.UniqueConstraint('MetadataId', 'Section', name='uq_metadata_section'),)

    def to_dict(self):
        return {
            'ClassId': self.ClassId,
            'Section': self.Section,
            'IsGradeFinalized': self.IsGradeFinalized,
            'MetadataId': self.MetadataId
        }
    
    # Adding a unique constraint
   
# Subject List
class Subject(db.Model):
    __tablename__ = 'SPSSubject'

    SubjectId = db.Column(db.Integer, primary_key=True, autoincrement=True)  
    SubjectCode = db.Column(db.String(20), unique=True) # Subject Code (COMP 20333, GEED 10013, ...)
    Name = db.Column(db.String(200)) # Subject Name
    Description = db.Column(db.String(200)) # Description of Subject
    Units = db.Column(db.Float) # Units of Subjects
    IsNSTP = db.Column(db.Boolean, default=False) # NSTP Cheker
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
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

# Class Subject contains the list of all subjects in the class
class ClassSubject(db.Model):
    __tablename__ = 'SPSClassSubject'

    ClassSubjectId = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    ClassId = db.Column(db.Integer, db.ForeignKey('SPSClass.ClassId', ondelete="CASCADE")) # Referencing to the Class
    SubjectId = db.Column(db.Integer, db.ForeignKey('SPSSubject.SubjectId', ondelete="CASCADE")) # Referencing to the Subject 
    FacultyId = db.Column(db.Integer, db.ForeignKey('FISFaculty.FacultyId', ondelete="CASCADE"), nullable=True) # Referencing to the Faculty
    Schedule = db.Column(db.String(100), nullable=True) # Schedule of Subjects
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Adding a unique constraint on the combination of ClassId, SubjectId, and FacultyId
    __table_args__ = (db.UniqueConstraint(
        'ClassId', 'SubjectId', 'FacultyId', name='_unique_class_subject_teacher'),)

    def to_dict(self):
        return {
            'ClassSubjectId': self.ClassSubjectId,
            'ClassId': self.ClassId,
            'SubjectId': self.SubjectId,
            'FacultyId': self.FacultyId,
            'Schedule': self.Schedule,
        }

# Student Class Subject Grade contains the student Class subject that they currently taking in
class StudentClassSubjectGrade(db.Model):
    __tablename__ = 'SPSStudentClassSubjectGrade'

    # StudentClassSubjectGradeId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ClassSubjectId = db.Column(db.Integer, db.ForeignKey('SPSClassSubject.ClassSubjectId', ondelete="CASCADE"), primary_key=True) # Reference to the class subject
    StudentId = db.Column(db.Integer, db.ForeignKey('SPSStudent.StudentId', ondelete="CASCADE"), primary_key=True) # Referencing to the student in subject taken
    Grade = db.Column(db.Float) # Students Grade
    DateEnrolled = db.Column(db.Date) # Date enrolled in the subject
    AcademicStatus = db.Column(db.Integer) # (1 - Passed, 2 - Failed, 3 - Incomplete or INC,  4 - Withdrawn, 5 - ReEnroll )
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'ClassSubjectId': self.ClassSubjectId,
            'StudentId': self.StudentId,
            'Grade': self.Grade,
            'DateEnrolled': self.DateEnrolled,
            'AcademicStatus': self.AcademicStatus,
        }

# Student Class Grade contains the average grade of student in class
class StudentClassGrade(db.Model):
    __tablename__ = 'SPSStudentClassGrade'
    
    StudentId = db.Column(db.Integer, db.ForeignKey('SPSStudent.StudentId', ondelete="CASCADE"), primary_key=True) # Referencing to Student
    ClassId = db.Column(db.Integer, db.ForeignKey('SPSClass.ClassId', ondelete="CASCADE"), primary_key=True) # Referencing to the Class
    Grade = db.Column(db.Float) # Average Grade
    Lister = db.Column(db.Integer, default=0) # 1 - President, 2 - Dean, 0 - Not Lister
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'StudentId': self.StudentId,
            'ClassId': self.ClassId,
            'Grade': self.Grade,
            'Lister': self.Lister
        }

# Class Subject Grade (SPS) for Analytics Response purposes
class ClassSubjectGrade(db.Model):
    __tablename__ = 'SPSClassSubjectGrade'

    ClassSubjectGradeId = db.Column(db.Integer, primary_key=True, autoincrement=True) # Class Subject Grade
    ClassSubjectId = db.Column(db.Integer, db.ForeignKey('SPSClassSubject.ClassSubjectId', ondelete="CASCADE"), unique=True) # Class Subject
    Grade = db.Column(db.Float) # Average Grade of Class Subject
    Passed = db.Column(db.Integer) # Amount of Passed
    Failed = db.Column(db.Integer) # Amount of Failed
    Incomplete = db.Column(db.Integer) # Amount of Incomplete
    Dropout = db.Column(db.Integer) # Amount of Dropout
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

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

# Average Grade of Class
class ClassGrade(db.Model):
    __tablename__ = 'SPSClassGrade'

    ClassGradeId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ClassId = db.Column(db.Integer, db.ForeignKey('SPSClass.ClassId', ondelete="CASCADE"), unique=True) # Class reference
    DeansLister = db.Column(db.Integer) # Amount of DeansLister
    PresidentsLister = db.Column(db.Integer) # Amount of PresidentsLister
    Grade = db.Column(db.Float) # Average Grade of the class
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'ClassGradeId': self.ClassGradeId,
            'ClassId': self.ClassId,
            'DeanLister': self.DeanLister,
            'PresidentLister': self.PresidentLister,
            'Grade': self.Grade
        }

# Average Grade of Course in specific year and semester
class CourseGrade(db.Model):
    __tablename__ = 'SPSCourseGrade'

    CourseGradeId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CourseId = db.Column(db.Integer, db.ForeignKey('SPSCourse.CourseId', ondelete="CASCADE")) # Referenccing to specific course
    Batch = db.Column(db.Integer, primary_key=True) # (2019, 2020, 2021, ...) - Batch course grades
    Semester = db.Column(db.Integer, primary_key=True, nullable=False) # (1, 2, 3) - Semester
    Grade = db.Column(db.Float) # Average grade of course
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'CourseGradeId': self.CourseGradeId,
            'CourseId': self.CourseId,
            'Year': self.Year,
            'Grade': self.Grade,
        }

# Curriculum is the list of subject that must taken of specific Course, Year, Semester and Batch. Subject automatically added in class when there is a curriculum
class Curriculum(db.Model):
    __tablename__ = 'SPSCurriculum'

    CurriculumId = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    SubjectId = db.Column(db.Integer, db.ForeignKey('SPSSubject.SubjectId', ondelete="CASCADE")) # Subejct that can be added in the classes if the same year, semester, course and batch
    MetadataId = db.Column(db.Integer, db.ForeignKey('SPSMetadata.MetadataId', ondelete="CASCADE"), nullable=False) # Metadata contains the year, semester, course and batch
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'CurriculumId': self.CurriculumId,
            'SubjectId': self.SubjectId,
            'MetadataId': self.MetadataId
            # Add other attributes if needed
        }
        

# This table will trigger everytime there is addded new batch semester
class LatestBatchSemester(db.Model):
    __tablename__ = 'SPSLatestBatchSemester'

    LatestBatchSemesterId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Batch = db.Column(db.Integer, nullable=False) # (2019, 2020, 2021, ...) - Batch course grades
    Semester = db.Column(db.Integer, nullable=False) # (1, 2, 3) - Semester
    IsEnrollmentStarted = db.Column(db.Boolean, default=False)
    IsGradeFinalized = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'LatestBatchSemesterId': self.LatestBatchSemesterId,
            'Batch': self.Batch,
            'Semester': self.Semester,
            'IsEnrollmentStarted': self.IsEnrollmentStarted,
            'IsGradeFinalized': self.IsGradeFinalized
            # Add other attributes if needed
        }


class RateLimit(db.Model):
    __tablename__ = 'RateLimit'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, unique=True)
    request_count = db.Column(db.Integer, default=0)
    last_request_timestamp = db.Column(db.DateTime, default=datetime.now)
    expiration_timestamp = db.Column(db.DateTime)


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('SPSSystemAdmin.SysAdminId', ondelete='CASCADE'))
    user = db.relationship('SystemAdmin')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)



class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('SPSSystemAdmin.SysAdminId', ondelete='CASCADE'))
    user = db.relationship('SystemAdmin')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('SPSStudent.StudentId', ondelete='CASCADE'))
    user = db.relationship('Student')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def is_refresh_token_active(self):
        print("REFRESH IS ACTIVE")
        if self.revoked:
            return False
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at >= time.time()
    
    def to_token_response(self):
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'access_token_revoked_at': int(self.access_token_revoked_at),
            'refresh_token_revoked_at': int(self.refresh_token_revoked_at),
            'scope': self.scope,
            'user_id': self.user_id
        }


# ------------------------------------------------
        
config_mode = os.getenv("CONFIG_MODE")
add_data = os.getenv("ADD_DATA")

# print('/'+config_mode+'/')
# print('/'+add_data+'/')

def init_db(app):
    db.init_app(app)
    
    if add_data=='True':
        print("Adding data")
        from data.student import student_data
        from data.faculty import faculty_data
        from data.registrar import registrar_data
        from data.studentRequirements import student_requirements_data
        from data.universityadmin import university_admin_data
        from data.systemadmin import system_admin_data
        from data.course import course_data
        from data.courseEnrolled import course_enrolled_data
        from data.subject import subject_data
        from data.classes import class_data
        from data.classSubject import class_subject_data
        from data.studentClassSubjectGrade import student_class_subject_grade_data
        from data.studentClassGrade import student_class_grade_data
        from data.classSubjectGrade import class_subject_grade_data
        from data.classGrade import class_grade_data
        from data.courseGrade import course_grade_data

        from data.curriculum import curriculum_data
        from data.metadata import metadata_data
        from data.latestBatchSemester import batch_semester_data

        def create_sample_data():
            for data in registrar_data:
                registrar = Registrar(**data)
                db.session.add(registrar)
            
            for data in student_data:
                student = Student(**data)
                db.session.add(student)
                
            for data in student_requirements_data:
                student_requirements = StudentRequirements(**data)
                db.session.add(student_requirements)

            # for data in faculty_data:
            #     faculty = Faculty(**data)
            #     db.session.add(faculty)

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

            for data in course_enrolled_data:
                course_enrolled = CourseEnrolled(**data)
                db.session.add(course_enrolled)
                db.session.flush()

            #### START THE COMMENT IF TESTING

            for data in metadata_data:
                metadata = Metadata(**data)
                db.session.add(metadata)
                db.session.flush()

            for data in curriculum_data:
                curriculum = Curriculum(**data)
                db.session.add(curriculum)
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
                
            for data in batch_semester_data:
                latest_batch_semester = LatestBatchSemester(**data)
                db.session.add(latest_batch_semester)
                db.session.flush()
            
            ### WITHOUT ANALYTICCS

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

    
    if config_mode == 'development' and add_data=='True':
        print("DEVELOPMENT AND ADDING DATA")
        with app.app_context():
            inspector = inspect(db.engine)
            if not inspector.has_table('SPSStudent'):
                db.create_all()
                create_sample_data()


    # if config_mode == 'development' :
    #     with app.app_context():
    #         inspector = inspect(db.engine)
    #         db.create_all()

    #         if add_data=='True':
    #             print("DEVELOPMENT AND ADDING DATA")
    #             create_sample_data()