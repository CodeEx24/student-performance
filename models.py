from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from flask_login import UserMixin
import os

import time
from flask_sqlalchemy import SQLAlchemy

from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)


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

    def get_user_id(self):
        return self.StudentId

# class Faculty(db.Model, UserMixin):
#     __tablename__ = 'Faculties'

#     TeacherId = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     TeacherNumber = db.Column(db.String(30), unique=True)  # UserID
#     Name = db.Column(db.String(50), nullable=False)  # Name
#     Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
#     Password = db.Column(db.String(128), nullable=False)  # Password
#     Gender = db.Column(db.Integer)  # Gender
#     DateOfBirth = db.Column(db.Date)  # DateOfBirth
#     PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
#     ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
#     MobileNumber = db.Column(db.String(11))  # MobileNumber
#     IsActive = db.Column(db.Boolean, default=True)

#     def to_dict(self):
#         return {
#             'TeacherId': self.TeacherId,
#             'TeacherNumber': self.TeacherNumber,
#             'Name': self.Name,
#             'Email': self.Email,
#             'Password': self.Password,
#             'Gender': self.Gender,
#             'DateOfBirth': self.DateOfBirth,
#             'PlaceOfBirth': self.PlaceOfBirth,
#             'ResidentialAddress': self.ResidentialAddress,
#             'MobileNumber': self.MobileNumber,
#             'IsActive': self.IsActive
#         }

#     def get_id(self):
#         return str(self.TeacherId)  # Convert to string to ensure compatibility


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

    def get_user_id(self):
        return self.SysAdminId
    


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
    TeacherId = db.Column(db.String(50), db.ForeignKey(
        'Faculty_Profile.faculty_account_id', ondelete="CASCADE"), nullable=True)
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



class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('SystemAdmins.SysAdminId', ondelete='CASCADE'))
    user = db.relationship('SystemAdmin')


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('SystemAdmins.SysAdminId', ondelete='CASCADE'))
    user = db.relationship('SystemAdmin')


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('Students.StudentId', ondelete='CASCADE'))
    user = db.relationship('Student')

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
        
class Faculty_Profile(db.Model, UserMixin):
    __tablename__ = 'Faculty_Profile'
    faculty_account_id = db.Column(db.String(50), primary_key=True)  # UserID
    faculty_type = db.Column(db.String(50), nullable=False)  # Faculty Type
    rank = db.Column(db.String(50))  # Faculty Rank
    units = db.Column(db.Numeric, nullable=False)  # Faculty Unit
    name = db.Column(db.String(50), nullable=False)  # Name
    first_name = db.Column(db.String(50), nullable=False)  # First Name
    last_name = db.Column(db.String(50), nullable=False)  # Last Name
    middle_name = db.Column(db.String(50))  # Middle Name
    middle_initial = db.Column(db.String(50))  # Middle Initial
    name_extension = db.Column(db.String(50))  # Name Extension
    birth_date = db.Column(db.Date, nullable=False)  # Birthdate
    date_hired = db.Column(db.Date, nullable=False)  # Date Hired
    degree = db.Column(db.String)  # Degree
    remarks = db.Column(db.String)  # Remarks
    faculty_code = db.Column(db.Integer, nullable=False)  # Faculty Code
    honorific = db.Column(db.String(50))  # Honorific
    age = db.Column(db.Numeric, nullable=False)  # Age
    email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    mobile_number = db.Column(db.String(128), nullable=False)  
    gender = db.Column(db.Integer, nullable=False)  # Gender
    password = db.Column(db.String(128), nullable=False)  # Password
    residential_address = db.Column(db.String(128))  # Password
    profile_pic = db.Column(db.String(50),default="14wkc8rPgd8NcrqFoRFO_CNyrJ7nhmU08")  # Profile Pic
    is_active = db.Column(db.Boolean, default=True) 
    
    # FOREIGN TABLES
    
    # PDS
    PDS_Personal_Details = db.relationship('PDS_Personal_Details')
    PDS_Contact_Details = db.relationship('PDS_Contact_Details')
    PDS_Family_Background = db.relationship('PDS_Family_Background')
    PDS_Educational_Background = db.relationship('PDS_Educational_Background')
    PDS_Eligibity = db.relationship('PDS_Eligibity')
    PDS_Work_Experience = db.relationship('PDS_Work_Experience')
    PDS_Voluntary_Work = db.relationship('PDS_Voluntary_Work')
    PDS_Training_Seminars = db.relationship('PDS_Training_Seminars')
    PDS_Outstanding_Achievements = db.relationship('PDS_Outstanding_Achievements')
    PDS_OfficeShips_Memberships = db.relationship('PDS_OfficeShips_Memberships')
    PDS_Agency_Membership = db.relationship('PDS_Agency_Membership')
    PDS_Teacher_Information = db.relationship('PDS_Teacher_Information')
    PDS_Additional_Questions = db.relationship('PDS_Additional_Questions')
    PDS_Character_Reference = db.relationship('PDS_Character_Reference')
    PDS_Signature = db.relationship('PDS_Signature')
    
    # SUBMODULES
    Evaluations = db.relationship('Evaluations')
    Awards = db.relationship('Awards')
    Qualifications = db.relationship('Qualifications')
    Publications = db.relationship('Publications')
    Conferences = db.relationship('Conferences')
    Announcement = db.relationship('Announcement')
    Research_Projects = db.relationship('Research_Projects')
    Advising = db.relationship('Advising')
    Mentoring = db.relationship('Mentoring')
    Committee = db.relationship('Committee')
    Collaboration_Opportunities = db.relationship('Collaboration_Opportunities')
    Professional_Development = db.relationship('Professional_Development')
    Feedback = db.relationship('Feedback')
    Teaching_Activities = db.relationship('Teaching_Activities')
    Assignment_Types = db.relationship('Assignment_Types')
    Teaching_Assignments = db.relationship('Teaching_Assignments')
    Mandatory_Requirements = db.relationship('Mandatory_Requirements')
    
    # TOKEN
    Login_Token = db.relationship('Login_Token')


    def to_dict(self):
        return {
            'faculty_account_id': self.faculty_account_id,
            'faculty_type': self.faculty_type,
            'rank': self.rank,
            'units': self.units,
            'name': self.name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'middle_name': self.middle_name,
            'middle_initial': self.middle_initial,
            'name_extension': self.name_extension,
            'birth_date': self.birth_date,
            'date_hired': self.date_hired,
            'degree': self.degree,
            'remarks': self.remarks,
            'faculty_code': self.faculty_code,
            'honorific': self.honorific,
            'age': self.age,
            'email': self.email,
            # 'password': self.password,
            'profile_pic': self.profile_pic,
            'is_active': self.is_active,
    
            # FOREIGN TABLES
            
            # PDS
            'PDS_Personal_Details': self.PDS_Personal_Details,
            'PDS_Contact_Details': self.PDS_Contact_Details,
            'PDS_Family_Background': self.PDS_Family_Background,
            'PDS_Educational_Background': self.PDS_Educational_Background,
            'PDS_Eligibity': self.PDS_Eligibity,
            'PDS_Work_Experience': self.PDS_Work_Experience,
            'PDS_Voluntary_Work': self.PDS_Voluntary_Work,
            'PDS_Training_Seminars': self.PDS_Training_Seminars,
            'PDS_Outstanding_Achievements': self.PDS_Outstanding_Achievements,
            'PDS_OfficeShips_Memberships': self.PDS_OfficeShips_Memberships,
            'PDS_Agency_Membership': self.PDS_Agency_Membership,
            'PDS_Teacher_Information': self.PDS_Teacher_Information,
            'PDS_Additional_Questions': self.PDS_Additional_Questions,
            'PDS_Character_Reference': self.PDS_Character_Reference,
            'PDS_Signature': self.PDS_Signature,
            
            # SUBMODULES
            'Evaluations': self.Evaluations,
            'Awards': self.Awards,
            'Qualifications': self.Qualifications,
            'Publications': self.Publications,
            'Conferences': self.Conferences,
            'Announcement': self.Announcement,
            'Research_Projects': self.Research_Projects,
            'Advising': self.Advising,
            'Mentoring': self.Mentoring,
            'Committee': self.Committee,
            'Collaboration_Opportunities': self.Collaboration_Opportunities,
            'Professional_Development': self.Professional_Development,
            'Feedback': self.Feedback,
            'Teaching_Activities': self.Teaching_Activities,
            'Assignment_Types': self.Assignment_Types,
            'Teaching_Assignments': self.Teaching_Assignments,
            'Mandatory_Requirements': self.Mandatory_Requirements,
            
            'Login_Token': self.Login_Token,

            
        }
        
    def get_id(self):
        return str(self.faculty_account_id)  # Convert to string to ensure compatibility
  
# Admin Profile 

class Admin_Profile(db.Model, UserMixin):
    __tablename__ = 'Admin_Profile'
    admin_account_id = db.Column(db.String(50), primary_key=True)  # UserID
    admin_type = db.Column(db.String(50), nullable=False)  # Faculty Type
    rank = db.Column(db.String(50))  # Faculty Rank
    units = db.Column(db.Numeric, nullable=False)  # Faculty Unit
    name = db.Column(db.String(50), nullable=False)  # Name
    first_name = db.Column(db.String(50), nullable=False)  # First Name
    last_name = db.Column(db.String(50), nullable=False)  # Last Name
    middle_name = db.Column(db.String(50))  # Middle Name
    middle_initial = db.Column(db.String(50))  # Middle Initial
    name_extension = db.Column(db.String(50))  # Name Extension
    birth_date = db.Column(db.Date, nullable=False)  # Birthdate
    date_hired = db.Column(db.Date, nullable=False)  # Date Hired
    degree = db.Column(db.String)  # Degree
    remarks = db.Column(db.String)  # Remarks
    faculty_code = db.Column(db.Integer, nullable=False)  # Faculty Code
    honorific = db.Column(db.String(50))  # Honorific
    age = db.Column(db.Numeric, nullable=False)  # Age
    email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    password = db.Column(db.String(128), nullable=False)  # Password
    profile_pic = db.Column(db.String(50),default="14wkc8rPgd8NcrqFoRFO_CNyrJ7nhmU08")  # Profile Pic
    is_active = db.Column(db.Boolean, default=True)    
    
    # FOREIGN TABLES
    
    PDS_Personal_Details = db.relationship('PDS_Personal_Details')
    PDS_Contact_Details = db.relationship('PDS_Contact_Details')
    PDS_Family_Background = db.relationship('PDS_Family_Background')
    PDS_Educational_Background = db.relationship('PDS_Educational_Background')
    PDS_Eligibity = db.relationship('PDS_Eligibity')
    PDS_Work_Experience = db.relationship('PDS_Work_Experience')
    PDS_Voluntary_Work = db.relationship('PDS_Voluntary_Work')
    PDS_Training_Seminars = db.relationship('PDS_Training_Seminars')
    PDS_Outstanding_Achievements = db.relationship('PDS_Outstanding_Achievements')
    PDS_OfficeShips_Memberships = db.relationship('PDS_OfficeShips_Memberships')
    PDS_Agency_Membership = db.relationship('PDS_Agency_Membership')
    PDS_Teacher_Information = db.relationship('PDS_Teacher_Information')
    PDS_Additional_Questions = db.relationship('PDS_Additional_Questions')
    PDS_Character_Reference = db.relationship('PDS_Character_Reference')
    PDS_Signature = db.relationship('PDS_Signature')
    
    Login_Token = db.relationship('Login_Token')
    
    def to_dict(self):
        return {
            'admin_account_id': self.admin_account_id,
            'admin_type': self.admin_type,
            'rank': self.rank,
            'units': self.units,
            'name': self.name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'middle_name': self.middle_name,
            'middle_initial': self.middle_initial,
            'name_extension': self.name_extension,
            'birth_date': self.birth_date,
            'date_hired': self.date_hired,
            'degree': self.degree,
            'remarks': self.remarks,
            'faculty_code': self.faculty_code,
            'honorific': self.honorific,
            'age': self.age,
            'email': self.email,
            'password': self.password,
            'profile_pic': self.profile_pic,
            'is_active': self.is_active,
            
            # PDS FOREIGN TABLES
        
            'PDS_Personal_Details': self.PDS_Personal_Details,
            'PDS_Contact_Details': self.PDS_Contact_Details,
            'PDS_Family_Background': self.PDS_Family_Background,
            'PDS_Educational_Background': self.PDS_Educational_Background,
            'PDS_Eligibity': self.PDS_Eligibity,
            'PDS_Work_Experience': self.PDS_Work_Experience,
            'PDS_Voluntary_Work': self.PDS_Voluntary_Work,
            'PDS_Training_Seminars': self.PDS_Training_Seminars,
            'PDS_Outstanding_Achievements': self.PDS_Outstanding_Achievements,
            'PDS_OfficeShips_Memberships': self.PDS_OfficeShips_Memberships,
            'PDS_Agency_Membership': self.PDS_Agency_Membership,
            'PDS_Teacher_Information': self.PDS_Teacher_Information,
            'PDS_Additional_Questions': self.PDS_Additional_Questions,
            'PDS_Character_Reference': self.PDS_Character_Reference,
            'PDS_Signature': self.PDS_Signature,
            
            'Login_Token': self.Login_Token,
        }
        
    def get_id(self):
        return str(self.admin_account_id)  # Convert to string to ensure compatibility
   
# SYSTEM ADMIN 

class System_Admin(db.Model, UserMixin):
    __tablename__ = 'System_Admin'
    sys_admin_id = db.Column(db.String(50), primary_key=True)  # UserID
    name = db.Column(db.String(50), nullable=False)  # Name
    email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    password = db.Column(db.String(128), nullable=False)  # Password
    profile_pic = db.Column(db.String(50),default="14wkc8rPgd8NcrqFoRFO_CNyrJ7nhmU08")  # Profile Pic  
    access_token = db.Column(db.String)
    refresh_token = db.Column(db.String)
    
    def to_dict(self):
        return {
            'sys_admin_id': self.sys_admin_id,
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'profile_pic': self.profile_pic,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
        }
        
    def get_id(self):
        return str(self.sys_admin_id)  # Convert to string to ensure compatibility

    
 # PDS Personal Details  
    
class PDS_Personal_Details(db.Model):
    __tablename__ = 'PDS_Personal_Details'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    sex = db.Column(db.String(50))  
    gender = db.Column(db.String(50)) 
    height = db.Column(db.Float)
    weight = db.Column(db.Float)  
    religion = db.Column(db.String(50))  
    civil_status = db.Column(db.String(50))  
    blood_type = db.Column(db.String(50))  
    pronoun = db.Column(db.String(50))  
    country = db.Column(db.String(50)) 
    city = db.Column(db.String(50)) 
    citizenship = db.Column(db.String(50)) 
    dual_citizenship = db.Column(db.String(50)) 
    remarks = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    
    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'sex': self.sex,
            'gender': self.gender,
            'height': self.height,
            'weight': self.weight,
            'religion': self.religion,
            'civil_status': self.civil_status,
            'blood_type': self.blood_type,
            'pronoun': self.pronoun,
            'country': self.country,
            'city': self.city,
            'citizenship': self.citizenship,
            'dual_citizenship': self.dual_citizenship,
            'remarks': self.remarks,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility

 # PDS Contact Details  
   
class PDS_Contact_Details(db.Model):
    __tablename__ = 'PDS_Contact_Details'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    email = db.Column(db.String(50))  
    mobile_number = db.Column(db.Numeric) 
    perm_country = db.Column(db.String(50))
    perm_region = db.Column(db.String(50))    
    perm_province = db.Column(db.String(50))  
    perm_city = db.Column(db.String(50))  
    perm_address = db.Column(db.String(50))  
    perm_zip_code = db.Column(db.Numeric)  
    perm_phone_number = db.Column(db.Numeric) 
    res_country = db.Column(db.String(50))
    res_region = db.Column(db.String(50))    
    res_province = db.Column(db.String(50))  
    res_city = db.Column(db.String(50))  
    res_address = db.Column(db.String(50))  
    res_zip_code = db.Column(db.Numeric)  
    res_phone_number = db.Column(db.Numeric) 
    remarks = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'email': self.email,
            'mobile_number': self.mobile_number,
            'perm_country': self.perm_country,
            'perm_region': self.perm_region,
            'perm_province': self.perm_province,
            'perm_city': self.perm_city,
            'perm_address': self.perm_address,
            'perm_zip_code': self.perm_zip_code,
            'perm_phone_number': self.perm_phone_number,
            'res_country': self.res_country,
            'res_region': self.res_region,
            'res_province': self.res_province,
            'res_city': self.res_city,
            'res_address': self.res_address,
            'res_zip_code': self.res_zip_code,
            'res_phone_number': self.res_phone_number,
            'remarks': self.remarks,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility

# PDS Family Background  
  
class PDS_Family_Background(db.Model):
    __tablename__ = 'PDS_Family_Background'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    full_name = db.Column(db.String(50))  
    relationship = db.Column(db.String(50))  
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'full_name': self.full_name,
            'relationship': self.relationship,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
    

# PDS Educational Background  
  
class PDS_Educational_Background(db.Model):
    __tablename__ = 'PDS_Educational_Background'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    school_name = db.Column(db.String(50))  
    level = db.Column(db.String(50))  
    from_date = db.Column(db.Date) 
    to_date = db.Column(db.Date)  
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'school_name': self.school_name,
            'level': self.level,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
    
    
# PDS Eligibity  
  
class PDS_Eligibity(db.Model):
    __tablename__ = 'PDS_Eligibity'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    eligibity = db.Column(db.String(50))  
    rating = db.Column(db.Float, default=0)  
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'eligibity': self.eligibity,
            'rating': self.rating,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
    

   
# PDS Work Experience  
  
class PDS_Work_Experience(db.Model):
    __tablename__ = 'PDS_Work_Experience'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    position = db.Column(db.String(50))  
    company_name = db.Column(db.String(50)) 
    status = db.Column(db.String(50)) 
    from_date = db.Column(db.Date) 
    to_date = db.Column(db.Date)   
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'position_title': self.position,
            'company_name': self.company_name,
            'status': self.status,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
    
# PDS Voluntary Work  
  
class PDS_Voluntary_Work(db.Model):
    __tablename__ = 'PDS_Voluntary_Work'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    organization = db.Column(db.String(50))  
    position = db.Column(db.String(50)) 
    from_date = db.Column(db.Date) 
    to_date = db.Column(db.Date)   
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'organization': self.organization,
            'position': self.position,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
  

# PDS Training & Seminars 
  
class PDS_Training_Seminars(db.Model):
    __tablename__ = 'PDS_Training_Seminars'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    title = db.Column(db.String(50))  
    level = db.Column(db.String(50)) 
    from_date = db.Column(db.Date) 
    to_date = db.Column(db.Date)   
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'title': self.title,
            'level': self.level,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
  

# PDS Outstanding Achievements
  
class PDS_Outstanding_Achievements(db.Model):
    __tablename__ = 'PDS_Outstanding_Achievements'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    achievement = db.Column(db.String(50))  
    level = db.Column(db.String(50)) 
    date = db.Column(db.Date) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'achievement': self.achievement,
            'level': self.level,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
  

# PDS OfficeShips/Memberships
  
class PDS_OfficeShips_Memberships(db.Model):
    __tablename__ = 'PDS_OfficeShips_Memberships'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    organization = db.Column(db.String(50))  
    position = db.Column(db.String(50)) 
    from_date = db.Column(db.Date) 
    to_date = db.Column(db.Date)   
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'organization': self.organization,
            'position': self.position,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
  

# PDS Agency Membership
  
class PDS_Agency_Membership(db.Model):
    __tablename__ = 'PDS_Agency_Membership'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    GSIS = db.Column(db.String(20))  
    PAGIBIG = db.Column(db.String(20)) 
    PHILHEALTH = db.Column(db.String(20)) 
    SSS = db.Column(db.String(20)) 
    TIN = db.Column(db.String(20)) 
    remarks = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'GSIS': self.GSIS,
            'PAGIBIG': self.PAGIBIG,
            'PHILHEALTH': self.PHILHEALTH,
            'SSS': self.SSS,
            'TIN': self.TIN,
            'remarks': self.remarks,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
  

# PDS Teacher Information
  
class PDS_Teacher_Information(db.Model):
    __tablename__ = 'PDS_Teacher_Information'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    information = db.Column(db.String(50)) 
    type = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'information': self.information,
            'type': self.type,
            'is_delete': self.is_delete,

        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     


# PDS Additional Questions
  
class PDS_Additional_Questions(db.Model):
    __tablename__ = 'PDS_Additional_Questions'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    
    q1_a = db.Column(db.String(50)) 
    q1_a_details = db.Column(db.String(50)) 
    
    q1_b = db.Column(db.String(50)) 
    q1_b_details = db.Column(db.String(50)) 
    
    q2_a = db.Column(db.String(50)) 
    q2_a_details = db.Column(db.String(50)) 
    
    q2_b = db.Column(db.String(50))
    q2_b_details = db.Column(db.String(50)) 
    
    q3 = db.Column(db.String(50))
    q3_details = db.Column(db.String(50)) 
    
    q4 = db.Column(db.String(50))
    q4_details = db.Column(db.String(50)) 
    
    q5_a = db.Column(db.String(50)) 
    q5_a_details = db.Column(db.String(50)) 
    
    q5_b = db.Column(db.String(50)) 
    q5_b_details = db.Column(db.String(50)) 
    
    q6 = db.Column(db.String(50)) 
    q6_details = db.Column(db.String(50)) 
    
    q7_a = db.Column(db.String(50))
    q7_a_details = db.Column(db.String(50)) 
    
    q7_b = db.Column(db.String(50))  
    q7_b_details = db.Column(db.String(50)) 
    
    q7_c = db.Column(db.String(50)) 
    q7_c_details = db.Column(db.String(50)) 
    
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            
            'q1_a': self.q1_a,
            'q1_a_details': self.q1_a_details,
            
            'q1_b': self.q1_b,
            'q1_b_details': self.q1_b_details,
            
            'q2_a': self.q2_a,
            'q2_a_details': self.q2_a_details,
            
            'q2_b': self.q2_b,
            'q2_b_details': self.q2_b_details,
            
            'q3': self.q3,
            'q3_details': self.q3_details,
            
            'q4': self.q4,
            'q4_details': self.q4_details,
            
            'q5_a': self.q5_a,
            'q5_a_details': self.q5_a_details,
            
            'q5_b': self.q5_b,
            'q5_b_details': self.q5_b_details,
            
            'q6': self.q6,
            'q6_details': self.q6_details,
            
            'q7_a': self.q7_a,
            'q7_a_details': self.q7_a_details,
            
            'q7_b': self.q7_b,
            'q7_b_details': self.q7_b_details,
            
            'q7_c': self.q7_c,
            'q7_c_details': self.q7_c_details,
            
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
    
# PDS Character Reference
  
class PDS_Character_Reference(db.Model):
    __tablename__ = 'PDS_Character_Reference'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    full_name = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'full_name': self.full_name,
            'is_delete': self.is_delete,
            
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
    
   
# PDS Signature
  
class PDS_Signature(db.Model):
    __tablename__ = 'PDS_Signature'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    wet_signature = db.Column(db.String(50)) 
    dict_certificate = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'wet_signature': self.wet_signature,
            'dict_certificate': self.dict_certificate,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility     
   
   
# LOGIN TOKEN
  
class Login_Token(db.Model):
    __tablename__ = 'Login_Token'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    access_token = db.Column(db.String)
    refresh_token = db.Column(db.String)
    is_delete = db.Column(db.Boolean, default=False) 

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            'admin_account_id': self.admin_account_id,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility
    
    
# FACULTY AND ADMIN SUBMODULES

# ------------------------------------------------
# EVALUATIONS
  
class Evaluations(db.Model):
    __tablename__ = 'Evaluations'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    feedback = db.Column(db.String) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'feedback': self.feedback,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# AWARDS
  
class Awards(db.Model):
    __tablename__ = 'Awards'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    award_name = db.Column(db.String) 
    date_received = db.Column(db.Date)
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'award_name': self.award_name,
            'date_received': self.date_received,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# QUALIFICATIONS
  
class Qualifications(db.Model):
    __tablename__ = 'Qualifications'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    degree = db.Column(db.String(50)) 
    certification = db.Column(db.String(50)) 
    area_expertise = db.Column(db.String) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'degree': self.degree,
            'certification': self.certification,
            'area_expertise': self.area_expertise,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# PUBLICATIONS
  
class Publications(db.Model):
    __tablename__ = 'Publications'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    title = db.Column(db.String(50)) 
    type = db.Column(db.String(50)) 
    date_published = db.Column(db.Date)
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'title': self.title,
            'type': self.type,
            'date_published': self.date_published,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# CONFERENCES
  
class Conferences(db.Model):
    __tablename__ = 'Conferences'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    conference_name = db.Column(db.String(50)) 
    date = db.Column(db.Date)
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'conference_name': self.conference_name,
            'date': self.date,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# ANNOUNCEMENT
  
class Announcement(db.Model):
    __tablename__ = 'Announcement'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    title = db.Column(db.String(50)) 
    content = db.Column(db.String) 
    date = db.Column(db.Date)
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'title': self.title,
            'content': self.content,
            'date': self.date,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# RESEARCH PROJECTS
  
class Research_Projects(db.Model):
    __tablename__ = 'Research_Projects'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    project_title = db.Column(db.String(50)) 
    status = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'project_title': self.project_title,
            'status': self.status,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# ADVISING
  
class Advising(db.Model):
    __tablename__ = 'Advising'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    student_id = db.Column(db.String(50)) 
    role = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'student_id': self.student_id,
            'role': self.role,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# MENTORING
  
class Mentoring(db.Model):
    __tablename__ = 'Mentoring'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    year = db.Column(db.String(50)) 
    course = db.Column(db.String(50)) 
    section = db.Column(db.String(50)) 
    number_students = db.Column(db.Integer) 
    type = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'year': self.year,
            'course': self.course,
            'section': self.section,
            'number_students': self.number_students,
            'type': self.type,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# COMMITTEES
  
class Committee(db.Model):
    __tablename__ = 'Committee'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    committee_name = db.Column(db.String(50)) 
    role = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'committee_name': self.committee_name,
            'role': self.role,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# COLLABORATION AND OPPORTUNITIES
  
class Collaboration_Opportunities(db.Model):
    __tablename__ = 'Collaboration_Opportunities'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    description = db.Column(db.String) 
    funding_source = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'description': self.description,
            'funding_source': self.funding_source,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# PROFESSIONAL DEVELOPMENT
  
class Professional_Development(db.Model):
    __tablename__ = 'Professional_Development'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    activity_type = db.Column(db.String(50)) 
    description = db.Column(db.String) 
    date = db.Column(db.Date) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'date': self.date,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# FEEDBACK
  
class Feedback(db.Model):
    __tablename__ = 'Feedback'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    feedback_type = db.Column(db.String(50)) 
    content = db.Column(db.String) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'activity_type': self.activity_type,
            'feedback_type': self.feedback_type,
            'content': self.content,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# TEACHING ACTIVITIES
  
class Teaching_Activities(db.Model):
    __tablename__ = 'Teaching_Activities'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    code = db.Column(db.String(50)) 
    course = db.Column(db.String(50)) 
    section = db.Column(db.String(50)) 
    subject = db.Column(db.String(50)) 
    status = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'code': self.code,
            'course': self.course,
            'section': self.section,
            'subject': self.subject,
            'status': self.status,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# ASSIGNMENT TYPES
  
class Assignment_Types(db.Model):
    __tablename__ = 'Assignment_Types'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True) # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    course = db.Column(db.String(50)) 
    section = db.Column(db.String(50)) 
    subject = db.Column(db.String(50)) 
    activity = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'course': self.course,
            'section': self.section,
            'subject': self.subject,
            'activity': self.activity,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# TEACHING ASSIGNMENTS
  
class Teaching_Assignments(db.Model):
    __tablename__ = 'Teaching_Assignments'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID
    semester = db.Column(db.String(50)) 
    code = db.Column(db.String(50)) 
    course = db.Column(db.String(50)) 
    section = db.Column(db.String(50)) 
    number_students = db.Column(db.String(50)) 
    course_load = db.Column(db.String(50)) 
    course_type = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'semester': self.semester,
            'code': self.code,
            'course': self.course,
            'section': self.section,
            'number_students': self.number_students,
            'course_load': self.course_load,
            'course_type': self.course_type,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------

# ------------------------------------------------
# MANDATORY REQUIREMENTS
  
class Mandatory_Requirements(db.Model):
    __tablename__ = 'Mandatory_Requirements'

    id = db.Column(db.Integer, primary_key=True)  # DataID
    faculty_account_id = db.Column(db.String(50), db.ForeignKey('Faculty_Profile.faculty_account_id'), nullable=True)  # FacultyID
    # admin_account_id = db.Column(db.String(50), db.ForeignKey('Admin_Profile.admin_account_id'), nullable=True)  # AdminID 
    requirement_item = db.Column(db.String(50)) 
    is_delete = db.Column(db.Boolean, default=False) 
    

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_account_id': self.faculty_account_id,
            # 'admin_account_id': self.admin_account_id,
            'requirement_item': self.requirement_item,
            'is_delete': self.is_delete
        }
        
    def get_id(self):
        return str(self.id)  # Convert to string to ensure compatibility  

# ------------------------------------------------
        
config_mode = os.getenv("CONFIG_MODE")
add_data = os.getenv("ADD_DATA")

# print('/'+config_mode+'/')
# print('/'+add_data+'/')

def init_db(app):
    db.init_app(app)
    
    if add_data=='False':
        print("Adding data")
        from data.data2.student import student_data
        # from data.data2.faculty import faculty_data

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
        # from data.data2.courseGrade import course_grade_data

        from data.data2.curriculum import curriculum_data
        from data.data2.metadata import metadata_data

        def create_sample_data():
            for data in student_data:
                student = Student(**data)
                db.session.add(student)

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

            # for data in course_grade_data:
            #     course_grade = CourseGrade(**data)
            #     db.session.add(course_grade)
            #     db.session.flush()

            
            db.session.commit()
            db.session.close()

    
    # if config_mode == 'development' :
    #     with app.app_context():
    #         inspector = inspect(db.engine)
    #         db.create_all()

    #         if add_data=='True':
    #             print("DEVELOPMENT AND ADDING DATA")
    #             create_sample_data()

    if config_mode == 'development' and add_data=='False':
        print("DEVELOPMENT AND ADDING DATA")
        with app.app_context():
            inspector = inspect(db.engine)
            if not inspector.has_table('Students'):
                db.create_all()
                create_sample_data()
