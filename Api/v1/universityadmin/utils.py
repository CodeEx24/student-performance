from models import StudentClassGrade, ClassGrade, Class, Course, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, db, UniversityAdmin, ClassSubjectGrade, Metadata, Curriculum
from sqlalchemy import desc
import re
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict
import datetime

from flask import session, jsonify
from static.js.utils import convertGradeToPercentage, checkStatus
from flask_mail import Message
from mail import mail
import pandas as pd
import random
import string
from sqlalchemy.orm import Session

from collections import defaultdict

def getCurrentUser():
    current_user_id = session.get('user_id')
    return UniversityAdmin.query.get(current_user_id)

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password
    

def getUniversityAdminData(str_univ_admin_id):
    try:
        data_university_admin = (
            db.session.query(UniversityAdmin).filter(
                UniversityAdmin.UnivAdminId == str_univ_admin_id).first()
        )

        if data_university_admin:
          

            dict_student_data = {
                "UnivAdminNumber": data_university_admin.UnivAdminNumber,
                "Name": data_university_admin.Name,
                "PlaceOfBirth": data_university_admin.PlaceOfBirth,
                "ResidentialAddress": data_university_admin.ResidentialAddress,
                "Email": data_university_admin.Email,
                "MobileNumber": data_university_admin.MobileNumber,
                "Gender": "Male" if data_university_admin.Gender == 1 else "Female",
            }

            return (dict_student_data)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def updateUniversityAdminData(str_univ_admin_id, email, number, residentialAddress):
    try:
        if not re.match(r'^[\w\.-]+@[\w\.-]+$', email):
            return {"type": "email", "status": 400}

        if not re.match(r'^09\d{9}$', number):
            return {"type": "mobile", "status": 400}

        if residentialAddress is None or residentialAddress.strip() == "":
            return {"type": "residential", "status": 400}

        # Update the student data in the database
        data_student = db.session.query(UniversityAdmin).filter(
            UniversityAdmin.UnivAdminId == str_univ_admin_id).first()
        
        if data_student:
            data_student.Email = email
            data_student.MobileNumber = number
            data_student.ResidentialAddress = residentialAddress
            db.session.commit()
                        
            return {"message": "Data updated successfully", "email": email, "number": number, "residentialAddress": residentialAddress, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}

def updatePassword(str_university_admin_id, password, new_password, confirm_password):
    try:
        data_student = db.session.query(UniversityAdmin).filter(
            UniversityAdmin.UnivAdminId == str_university_admin_id).first()

        if data_student:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_student.Password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(
                    new_password)
                data_student.Password = new_hashed_password
                db.session.commit()
                return {"message": "Password changed successfully", "status": 200}

            else:
                return {"message": "Changing Password was unsuccessful. Please try again.", "status": 400}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}



def getEnrollmentTrends():
    try:
        # Query data with required fields
        data_course_enrolled = db.session.query(
            Course.CourseCode, CourseEnrolled.DateEnrolled
        ).join(Course, Course.CourseId == CourseEnrolled.CourseId).order_by(CourseEnrolled.DateEnrolled).all()

        if data_course_enrolled:
            # Create a dictionary to store year-wise course counts
            course_year_counts = defaultdict(lambda: defaultdict(int))

            # Iterate through the data to calculate counts
            for course_code, date_enrolled in data_course_enrolled:
                year_enrolled = date_enrolled.year
                course_year_counts[year_enrolled][course_code] += 1

            # Convert the counts to a list of dictionaries with the desired format
            trend_data = {
                "CourseDetails": [],
                "LowestEnrolledCount": None,
                "HighestEnrolledCount": None,
                "LowestEnrolledCourses": [],
                "HighestEnrolledCourses": [],
                "TotalEnrolled": None
            }

            # Find lowest, highest, and total enrollment counts
            for year, course_counts in course_year_counts.items():
                trend_item = {"x": year, **course_counts}
                trend_data["CourseDetails"].append(trend_item)

            if trend_data["CourseDetails"]:
                total_enrolled = sum(course for year_counts in course_year_counts.values() for course in year_counts.values())
                trend_data["TotalEnrolled"] = total_enrolled

                # Find the lowest and highest enrolled counts and their corresponding courses
                lowest_enrolled_count = min(course for year_counts in course_year_counts.values() for course in year_counts.values())
                highest_enrolled_count = max(course for year_counts in course_year_counts.values() for course in year_counts.values())

                for year_counts in course_year_counts.values():
                    for course_code, count in year_counts.items():
                        course_name = db.session.query(Course.Name).filter_by(
                            CourseCode=course_code).first()

                        if count == lowest_enrolled_count:
                            trend_data["LowestEnrolledCount"] = count
                            trend_data["LowestEnrolledCourses"].append(
                                course_name[0] if course_name else course_code)

                        if count == highest_enrolled_count:
                            trend_data["HighestEnrolledCount"] = count
                            trend_data["HighestEnrolledCourses"].append(
                                course_name[0] if course_name else course_code)

            return trend_data
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None



def getCurrentGpaGiven():
    try:
        data_course_gpa = db.session.query(
            CourseGrade).order_by(CourseGrade.Year).all()

        if data_course_gpa:
            course_year_grades = defaultdict(list)

            for course_gpa in data_course_gpa:
                year = course_gpa.Year
                grade = course_gpa.Grade

                course_year_grades[year].append(grade)

            # Find the latest year
            latest_year = max(course_year_grades.keys())

            # Calculate the average Grade for the latest year
            if latest_year in course_year_grades:
                latest_year_grades = course_year_grades[latest_year]
                average_grade = sum(latest_year_grades) / \
                    len(latest_year_grades)
                # Format the average Grade to two decimal places
                average_grade = round(average_grade, 2)
            else:
                average_grade = None

            return {"AverageGrade": average_grade}
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getOverallCoursePerformance():
    try:
        data_course_grade = db.session.query(
            CourseGrade, Course).join(Course, Course.CourseId == CourseGrade.CourseId).order_by(CourseGrade.Year, CourseGrade.CourseId).all()
        if data_course_grade:
            course_year_grades = defaultdict(dict)

            for course_grade in data_course_grade:
                year = course_grade.CourseGrade.Year
                course_id = course_grade.Course.CourseCode
                
                grade = convertGradeToPercentage(course_grade.CourseGrade.Grade)

                if year not in course_year_grades:
                    course_year_grades[year] = {"x": year}

                course_year_grades[year][course_id] = grade

            # Convert the data into a list of dictionaries
            formatted_data = list(course_year_grades.values())
            return formatted_data
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getAllClassData():
    try:
        current_year = datetime.datetime.now().year

        data_class_subject_grade_handle = (
            db.session.query(   
                Class, Course, ClassGrade
            )
            .join(Course, Course.CourseId == Class.CourseId)
            .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
            # .filter(Class.Batch == current_year - 1)
            .order_by(desc(Class.Batch), desc(Class.CourseId), Class.Year, Class.Section)
            .all()
        )

        if data_class_subject_grade_handle:
            list_classes = []
            seen_class_ids = set()  # Initialize a set to track seen ClassIds

            for class_subject_grade in data_class_subject_grade_handle:
                class_id = class_subject_grade.Class.ClassId

                # Check if the ClassId is not in the seen_class_ids set
                if class_id not in seen_class_ids:
                    # Get the class name
                    # Check if Grade exists
                    if class_subject_grade.ClassGrade.Grade is not None:
                        # If Grade exists, format it with two decimal places
                        grade_value = f"{class_subject_grade.ClassGrade.Grade:.2f}"
                    else:
                        # If Grade does not exist, set it to 'N/A'
                        grade_value = "N/A"
                        
                    class_obj = {
                        'ClassId': class_id,
                        'ClassName': f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Class.Year}-{class_subject_grade.Class.Section}",
                        'Semester': class_subject_grade.Class.Semester,
                        "Course": class_subject_grade.Course.Name,
                        "Batch": class_subject_grade.Class.Batch,
                        "Grade": grade_value
                    }

                    # Add class_id to the seen_class_ids set
                    seen_class_ids.add(class_id)

                    # Add class_obj to the list_classes
                    list_classes.append(class_obj)

            # Return the list of class objects
            return {'Classes': list_classes}
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getClassPerformance(class_id):
    try:
        class_grade = (
            db.session.query(
                ClassGrade, Course, Class
            )
            .join(Class, Class.ClassId == ClassGrade.ClassId)
            .join(Course, Class.CourseId == Course.CourseId)
            .filter(ClassGrade.ClassId == class_id)
            .first()
        )

        
        if class_grade:

            # Calculate class name
            class_name = f"{class_grade.Course.CourseCode} {class_grade.Class.Year}-{class_grade.Class.Section} ({class_grade.Class.Batch})"
            num_class_batch = class_grade.Class.Batch
            num_class_section = class_grade.Class.Section

            dict_class_grade = {
                'Class': class_name,
                'Batch': num_class_batch,
                'ListGrade': [],
                'PresidentLister': class_grade.ClassGrade.PresidentsLister,
                'DeanLister': class_grade.ClassGrade.DeansLister
            }
            
            list_grade = []
            for i in range(1, class_grade.Class.Year+1):
                batch = class_grade.Class.Batch - class_grade.Class.Year + i
                class_grade_result = (
                    db.session.query(
                        Class,
                        ClassGrade,
                    )
                    .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                    .filter(Class.Year == i, Class.Batch == batch, Class.Section == num_class_section)
                    .first()

                )

                list_grade.append(
                    {'x': class_grade_result.Class.Batch, 'y': convertGradeToPercentage(class_grade_result.ClassGrade.Grade)})
                
            dict_class_grade['ListGrade'].extend(list_grade)

            return (dict_class_grade)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None



def processAddingStudents(file):
    try:
        # Check if the file is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400


        # Read the Excel file into a DataFrame
        df = pd.read_excel(file)
        
        # dict data list
        list_student_data = []
        # Add a dict of already existing students
        list_existing_data = []
        # Add a dict of already existing students emai
        
        # For example, you can iterate through rows and access columns like this:
        for index, row in df.iterrows():
            # Extract the values from the DataFrame
            student_number = row['Student Number'] # OK
            student_name = row['Name']
            student_email = row['Email']
            student_mobile =  str(row['Phone Number'])
            student_address = row['Address'] # OK
            # Check if Gender is Male it is 1 else it is 2
            
            student_gender = row['Gender'] # OK
            student_course = row['Course Code']
            student_date_enrolled = row['Date Enrolled'].date()
            student_batch = row['Batch'] # OK
        
            
            # Check if the student is already exist in the database based on StudentNumber or Email
            student_number_data = db.session.query(Student).filter(
                (Student.StudentNumber == student_number) 
            ).first()
            student_email_data = db.session.query(Student).filter(
                (Student.Email == student_email) 
            ).first()

            if not student_number_data and not student_email_data:
                password = generate_password()
                gender = 1 if student_gender == 'Male' else (2 if student_gender == 'Female' else None)

                print(gender)
                course = db.session.query(Course).filter_by(CourseCode=student_course).first()

              # Add the new student in the database

                # Ensure the mobile number has a leading zero
                if not student_mobile.startswith('0'):
                    student_mobile = '0' + student_mobile

                new_student = Student(
                    StudentNumber=student_number,
                    Name=student_name,
                    Email=student_email,
                    MobileNumber=str(student_mobile),
                    ResidentialAddress=student_address,
                    Gender=gender,
                    Password=generate_password_hash(password)
                )


                db.session.add(new_student)
                db.session.flush()
                
                print('new_student: ', new_student)
                # Using the course above generate a CourseEnrolled for students
                new_course_enrolled = CourseEnrolled(
                    CourseId=course.CourseId,
                    StudentId=new_student.StudentId,
                    DateEnrolled=student_date_enrolled,
                    Status=1,
                    CurriculumYear=student_batch
                )
                
                # # Add the new course enrolled to the session
                db.session.add(new_course_enrolled)
                # db.session.commit()
                
                msg = Message('Your current PUP Account has been granted.', sender='your_email@example.com',
                            recipients=[str(new_student.Email)])
                # The message body should be the credentials details
                msg.body = f"Your current PUP Account has been granted. \n\n Email: {str(new_student.Email)} \n Password: {str(new_student.Password)} \n\n Please change your password after you log in. \n\n Thank you."
                
                mail.send(msg)
                
                print('student_gender: ', student_gender)
                # Append the student data in list data in format of dict
                if not gender:
                    list_student_data.append({
                        "Email": str(student_email),
                        "Gender": "N/A",
                        "Mobile Number": str(student_mobile),
                        "Name": str(student_name),
                        "Student Number": str(student_number)
                    })
                else:
                    list_student_data.append({
                        "Email": str(student_email),
                        "Gender": student_gender,
                        "Mobile Number": str(student_mobile),
                        "Name": str(student_name),
                        "Student Number": str(student_number)
                    })
             
            else:
                # Append the student nummber
                list_existing_data.append({'StudentNumber':student_number, 'StudentEmail': student_email})
                # Remove all existing db.session
                
        if list_existing_data:
            db.session.rollback()
            return jsonify({'error': 'The following student number or email already exist in the database ', 'existing_data': list_existing_data}), 500
        else:        
            db.session.commit()
            return  jsonify({'result': 'Data added successfully', 'data': list_student_data}), 200
            
    except Exception as e:
        # print the error
        print(e)
        db.session.rollback()
        return jsonify({'error': 'An error occurred while processing the file'}), 500
    
def processAddingClass(file):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        list_new_class_data = []
        list_course_not_exist = []
        curriculum_not_exist = []
        class_data_exist = []

        with db.session.begin():
            for index, row in df.iterrows():
                course_code = row['Course Code']
                section = int(row['Section'])
                year = int(row['Year Level'])
                semester = int(row['Semester'])
                batch = int(row['Batch'])

                course = db.session.query(Course).filter_by(CourseCode=course_code).first()
                
                if not course:
                    if course_code not in list_course_not_exist:
                        list_course_not_exist.append(course_code)
                    continue
                        
                metadata = db.session.query(Metadata).filter_by(CourseId=course.CourseId, YearLevel=year, Semester=semester, Batch=batch).first()

                if not metadata:
                    curriculum_not_exist.append({
                        "CourseCode": course_code,
                        "Year": year,
                        "Semester": semester,
                        "Batch": batch
                    })

                if course and metadata:
                    curriculum = db.session.query(Curriculum).filter_by(MetadataId=metadata.MetadataId).all()
                    if curriculum:
                        class_data = db.session.query(Class).filter_by(
                            CourseId=course.CourseId, Year=year, Section=section, Semester=semester, Batch=batch).first()

                        if not class_data:
                            class_name = f"{course_code} {year}-{section}"
                            course_name = course.Name
                            new_class = Class(
                                CourseId=course.CourseId,
                                Year=year,
                                Section=section,
                                Semester=semester,
                                Batch=batch,
                                IsGradeFinalized=False
                            )

                            db.session.add(new_class)
                            db.session.flush()
                            new_class_grade = ClassGrade(
                                ClassId=new_class.ClassId,
                                DeansLister=0,
                                PresidentsLister=0,
                                Grade=0
                            )

                            db.session.add(new_class_grade)
                            
                            # list_new_class_data add the new class data
                            list_new_class_data.append({
                                "ClassId": new_class.ClassId,
                                "ClassName": class_name,
                                "Course": course_name,
                                "Grade": 'N/A',
                                "Semester": new_class.Semester,
                                "Batch": new_class.Batch
                            })
                            
                            for cur in curriculum:
                                new_class_subject = ClassSubject(
                                    ClassId=new_class.ClassId,
                                    SubjectId=cur.SubjectId
                                )
                                db.session.add(new_class_subject)
                                db.session.flush()
                                new_class_subject_grade = ClassSubjectGrade(
                                    ClassSubjectId=new_class_subject.ClassSubjectId,
                                    Grade=0,
                                    Passed=0,
                                    Failed=0,
                                    Incomplete=0,
                                    Dropout=0
                                )

                                db.session.add(new_class_subject_grade)
                        else:
                            # class_data_exist append it
                            class_data_exist.append({
                                "CourseCode": course_code,
                                "Year": year,
                                "Section": section,
                                "Batch": batch,
                                "Semester": semester
                            })
                    else:
                        curriculum_not_exist.append({
                            "CourseCode": course_code,
                            "Year": year,
                            "Section": section,
                            "Batch": batch,
                            "Semester": semester
                        })
                else:   
                    print('list_course_not_exist: ')
                    
            if list_course_not_exist or curriculum_not_exist or class_data_exist:
                db.session.rollback()
                error_message = 'Something went wrong in processing the files'
                
                errors = {
                    'list_course_not_exist': list_course_not_exist,
                    'curriculum_not_exist': curriculum_not_exist,
                    'class_data_exist': class_data_exist
                }
                
                return jsonify({'error': error_message, 'errors': errors}), 400
            else:
                db.session.commit()
                return jsonify({'result': 'Data added successfully', 'data': list_new_class_data}), 200
 
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'error': 'An error occurred while processing the file'}), 500

    #         if course:
    #             # Check if year is current year or + 1 only
    #             current_year = datetime.datetime.now().year
        
    #             if batch != current_year and batch != current_year + 1:
    #                 return jsonify({'error': 'Invalid year. Please select the current year or the next year.'}), 400
                
    #             # Check if course.id, year, section, semester and batch already existing in class
    #             class_data = db.session.query(Class).filter(
    #                 Class.CourseId == course.CourseId, Class.Year == year, Class.Section == section, Class.Semester == semester, Class.Batch == batch).first()
          
    #             # If existing throw an error
    #             if not class_data:             
    #                 new_class = Class(
    #                     CourseId=course.CourseId,
    #                     Year=year,
    #                     Section=section,
    #                     Semester=semester,
    #                     Batch=batch, 
    #                     IsGradeFinalized=False
    #                 )
                    
    #                 # Just add in session
    #                 db.session.add(new_class)
    #                 db.session.flush()
                    
                    
                    
    #                 # Make a ClassGrade
    #                 new_class_grade = ClassGrade(
    #                     ClassId=new_class.ClassId,
    #                     PresidentsLister=0,
    #                     DeansLister=0,
    #                     Grade= 5.00
    #                 )
    #                 db.session.add(new_class_grade)
                    
    #                 # Combine the course_code, year, section to class_name variable
    #                 class_name = f"{course_code} {year}-{section}"
    #                 list_class_data.append({'ClassId':new_class.ClassId,'ClassName':class_name,'Batch':batch, 'Course': course.Name, 'Grade': 'N/A'})
    #             else:
    #                 list_existing_class_data.append({
    #                     'CourseCode': course_code,
    #                     "Year": year,
    #                     "Section": section,
    #                     "Batch": batch,
    #                     "Semester": semester
    #                 })
    #         else:
    #             # check if course_code not existing in list_missing_course
    #             if course_code not in list_missing_courses:
    #                 list_missing_courses.append(course_code)
                
    #     if list_existing_class_data:
    #         db.session.rollback()
    #         return jsonify({'error': 'The class already exist in the database', 'existing_data': list_existing_class_data}), 500
    #     elif list_missing_courses:
    #         db.session.rollback()
    #         return jsonify({'error': 'Course Code does not exist in the database', 'missing_course': list_missing_courses}), 400  
    #     else:
    #         db.session.rollback()
    #         # db.session.commit()
    #         return jsonify({'result': "Data added successfully", 'data':list_class_data }), 200   
    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({'error': 'An error occurred while processing the file'}), 500
    

 
def processClassStudents(file, class_id):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        list_student_added = []
        list_student_number_not_exist = []
        list_student_class_subject_exist = []
        
        # Find the class
        class_data = db.session.query(Class).filter_by(ClassId=class_id).first()
        if class_data:
            class_subject_data = db.session.query(ClassSubject).filter_by(ClassId=class_id).all()
            if class_subject_data:
                # for loop the class_subject_data
                for class_subject in class_subject_data:                    
                    # Create StudentClassSubjectGrade for all ClassSubjectId
                    for index, row in df.iterrows():
                        student_number = row['Student Number']
                        date_enrolled = row['Date Enrolled'].date()
                        
                        # Get the student data
                        student_data = db.session.query(Student).filter_by(StudentNumber=student_number).first()
                        if student_data:
                            # Check if student_class_subject_grade exist
                            student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId=student_data.StudentId, ClassSubjectId=class_subject.ClassSubjectId).first()
                            if student_class_subject_grade:
                                # Find the subject 
                                subject_data = db.session.query(Subject).filter_by(SubjectId=class_subject.SubjectId).first()
                        
                                list_student_class_subject_exist.append({
                                    "StudentNumber": student_number,
                                    "SubjectCode": subject_data.SubjectCode
                                }) 
                            else:
                                subject_data = db.session.query(Subject).filter_by(SubjectId=class_subject.SubjectId).first()
                                
                                new_student_class_subject_grade = StudentClassSubjectGrade(
                                    StudentId=student_data.StudentId,
                                    ClassSubjectId=class_subject.ClassSubjectId,
                                    DateEnrolled=date_enrolled
                                )
                                db.session.add(new_student_class_subject_grade)
                                db.session.commit()
                                
                                # Append list_student_added
                                list_student_added.append({
                                    "StudentNumber": student_number,
                                    "SubjectCode": subject_data.SubjectCode
                                })
                        else:
                            if student_number not in list_student_number_not_exist:
                                list_student_number_not_exist.append(student_number)   
            else:
                # return no class subject yet
                return jsonify({'error': 'No class subject yet'}), 400
        else:
            # return error with message cannot find the class
            return jsonify({'error': 'Cannot find the class'}), 400
        
        if list_student_number_not_exist:
            print("list_student_number_not_exist: TRUE", )
            
        if list_student_class_subject_exist:
            print("list_student_class_subject_exist: TRUE", )
            
        if not list_student_added:
            print("list_student_added: TRUE", )
        
        # Check if length of list_student_number_not_exist or list_student_class_subject_exist
        if (list_student_number_not_exist or list_student_class_subject_exist) and list_student_added:
            db.session.rollback()
            return jsonify({'error': 'Some data cannot be added', 'errors': {'student_number_not_exist': list_student_number_not_exist, 'student_class_subject_exist': list_student_class_subject_exist}}), 400
        elif (list_student_number_not_exist or list_student_class_subject_exist) and not list_student_added:
            db.session.rollback()
            return jsonify({'error': 'Adding students failed', 'errors': {'student_number_not_exist': list_student_number_not_exist, 'student_class_subject_exist': list_student_class_subject_exist}}), 400
        else:
            return jsonify({'result': 'Data added successfully'}), 200

    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'error': 'An error occurred while processing the file'}), 500


def getStudentData():
    try:
        data_student = (
            db.session.query(Student).all()
        )

        
        if data_student:
             # For loop the data_student and put it in dictionary
            list_student_data = []
            for student in data_student:
                dict_student = {
                    "Student Number": student.StudentNumber,
                    "Name": student.Name,
                    "Email": student.Email,
                    "Mobile Number": student.MobileNumber,
                    "Gender": "Male" if student.Gender == 1 else "Female",
                }
                # Append the data
                list_student_data.append(dict_student)
            return (list_student_data)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
    
def getAllClassSubjectData():
    try:
        data_class_subject = (
            db.session.query(ClassSubject, Subject, Class, Course, Faculty).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).join(Class, Class.ClassId == ClassSubject.ClassId).join(Course, Course.CourseId == Class.CourseId).join(Faculty, Faculty.TeacherId == ClassSubject.TeacherId).order_by(desc(Class.Batch),desc(Class.Semester), (Subject.Name)).all()
        )
        

        
        if data_class_subject:
                # For loop the data_student and put it in dictionary
            list_class_subject = []
            for class_subject in data_class_subject:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_subject.Course.CourseCode} {class_subject.Class.Year}-{class_subject.Class.Section}"
                
                dict_class_subject = {
                    "Section Code": class_name,
                    "Subject": class_subject.Subject.Name,
                    "Teacher": class_subject.Faculty.Name,
                    "Schedule": class_subject.ClassSubject.Schedule,
                    'Batch': class_subject.Class.Batch,
                    'Semester': class_subject.Class.Semester
                }
                # # Append the data
                list_class_subject.append(dict_class_subject)
            return jsonify({'result': list_class_subject})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
def getClassSubject(class_id):
    try:
        data_class_subject = (
            db.session.query(Class, ClassSubject, Subject, ClassSubjectGrade, Course)
            .join(ClassSubject, ClassSubject.ClassId == Class.ClassId)
            .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
            .join(Course, Course.CourseId == Class.CourseId)
            .join(ClassSubjectGrade, ClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .filter(ClassSubject.ClassId == class_id)
            .all()
        )

        if data_class_subject:
            # For loop the data_student and put it in dictionary
            list_class_subject = []
            for class_subject in data_class_subject:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_subject.Course.CourseCode} {class_subject.Class.Year}-{class_subject.Class.Section}"

                # Check if the class_subject.TeacherId exists, if yes, make a query for it
                if class_subject.ClassSubject.TeacherId or class_subject.ClassSubject.Schedule:
                    teacher_id = 0
                    if class_subject.ClassSubject.TeacherId:
                        teacher = db.session.query(Faculty).filter(Faculty.TeacherId == class_subject.ClassSubject.TeacherId).first()
                        if teacher:
                            teacher_id = teacher.TeacherId

                    schedule = class_subject.ClassSubject.Schedule if class_subject.ClassSubject.Schedule else None
                else:
                    teacher_id = None
                    schedule = None

                dict_class_subject = {
                    "ClassSubjectId": class_subject.ClassSubject.ClassSubjectId,
                    "SubjectCode": class_subject.Subject.SubjectCode,
                    "Section Code": class_name,
                    "Grade": round(class_subject.ClassSubjectGrade.Grade, 2) if class_subject.ClassSubjectGrade else None,
                    "Subject": class_subject.Subject.Name,
                    "TeacherId": teacher_id,
                    "Schedule": schedule,
                    'Batch': class_subject.Class.Batch if class_subject.Class else None,
                }

                # Append the data
                list_class_subject.append(dict_class_subject)

            return jsonify({'data': list_class_subject})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
def getClassDetails(class_id):
    try:
        data_class_details = db.session.query(Class, Course).join(Course, Course.CourseId == Class.CourseId).filter(Class.ClassId == class_id).all()
        
        if data_class_details:
                # For loop the data_student and put it in dictionary
            for class_details in data_class_details:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_details.Course.CourseCode} {class_details.Class.Year}-{class_details.Class.Section}"

                dict_class_details = {
                    "Course": class_details.Course.Name,
                    "Section Code": class_name,
                    'Batch': class_details.Class.Batch,
                    "Semester": class_details.Class.Semester
                }
                return jsonify({'data': dict_class_details})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def getStudentClassSubjectData(classSubjectId):
    try:
        data_class_details = db.session.query(ClassSubject).filter_by(ClassSubjectId = classSubjectId).first()
        # Get the StudentClassSubjectGrade
        print('data_class_details: ', data_class_details)
        if data_class_details:
            data_student_subject_grade = db.session.query(StudentClassSubjectGrade, Student).join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId).filter(StudentClassSubjectGrade.ClassSubjectId == data_class_details.ClassSubjectId).all()
            print('data_student_subject_grade: ', data_student_subject_grade)
            if data_student_subject_grade:
                list_student_data = []
                    # For loop the data_student and put it in dictionary
                for student_subject_grade in data_student_subject_grade:
                    dict_student_subject_grade = {
                        "ClassSubjectId": student_subject_grade.StudentClassSubjectGrade.ClassSubjectId,
                        "StudentId": student_subject_grade.Student.StudentId,
                        "StudentNumber": student_subject_grade.Student.StudentNumber,
                        "Name": student_subject_grade.Student.Name,
                        "Email": student_subject_grade.Student.Email,
                        "Grade": student_subject_grade.StudentClassSubjectGrade.Grade
                    }
                    list_student_data.append(dict_student_subject_grade)
                return  jsonify({'data': list_student_data})
            else:
                return jsonify({'data': [], 'message': "No students"})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None
    
def deleteStudent(class_subject_id, student_id):
    try:
        student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(ClassSubjectId = class_subject_id, StudentId = student_id).first()
        
        if student_class_subject_grade:
            db.session.delete(student_class_subject_grade)
            db.session.commit()
            return jsonify({'result': 'Data deleted successfully'})
        else:
            return jsonify({'error': 'Data cannot be deleted'})
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    # getCurriculumSubject

def getCurriculumData():
    try:
        metadata = db.session.query(Curriculum, Metadata, Course, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).order_by(desc(Metadata.Batch), desc(Metadata.YearLevel)).all()
        
        # Get the StudentClassSubjectGrade
        if metadata:
            list_metadata = []
                # For loop the data_student and put it in dictionary
            for data in metadata:
                # Convert the YearLevel to 1st, 2nd, 3rd, 4th
                
                
                dict_metadata = {
                    "MetadataId": data.Metadata.MetadataId,
                    "Year": data.Metadata.YearLevel,
                    "Semester": data.Metadata.Semester,
                    "Batch": data.Metadata.Batch,
                    "Course": data.Course.CourseCode,
                    # "Subject": data.Subject.Name,
                    "Subject Code": data.Subject.SubjectCode
                }
                list_metadata.append(dict_metadata)
            return  jsonify({'data': list_metadata})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    

def getCurriculumSubject(metadata_id):
    try:
        curriculum_subjects = db.session.query(Curriculum, Subject).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Curriculum.MetadataId == metadata_id).all()
        # Get the StudentClassSubjectGrade
        if curriculum_subjects:
            list_curriculum_subjects = []
                # For loop the data_student and put it in dictionary
            for data in curriculum_subjects:
                dict_curriculum_subjects = {
                    "Subject Code": data.Subject.SubjectCode,
                    "Name": data.Subject.Name,
                    "Units": "{:.2f}".format(round(data.Subject.Units, 2))
                }
                list_curriculum_subjects.append(dict_curriculum_subjects)
            return  jsonify({'data': list_curriculum_subjects})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    

def getActiveTeacher():
    try:
        active_teacher = db.session.query(Faculty).filter_by(IsActive = True).all()
        # Get the StudentClassSubjectGrade
        if active_teacher:
            list_active_teacher = []
                # For loop the active_teacher and put it in dictionary
            for data in active_teacher:
                dict_active_teacher = {
                    "TeacherId": data.TeacherId,
                    "TeacherName": data.Name,
                }
                list_active_teacher.append(dict_active_teacher)
            return  jsonify({'data': list_active_teacher})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def processAddingCurriculumSubjects(file):

    # Check if the file is empty
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Check file extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

    # Read the Excel file into a DataFrame
    df = pd.read_excel(file)

    # dict data list
    list_curriculum_subjects = []
    # Add a dict of already existing students
    list_curriculum_subjects_exist = []
    list_subject_code_not_exist = []
    not_existing_course = []
    # Add a dict of already existing students emai
    # For example, you can iterate through rows and access columns like this:
    for index, row in df.iterrows():
        # Extract the values from the DataFrame
        course_code = row['Course']
        subject_code = row['Subject Code']
        year_level = row['Year']
        semester = row['Semester']
        batch = row['Batch']
    
        course = db.session.query(Course).filter_by(CourseCode = course_code).first()
            
        # Check if course existing
        if not course:
            # Check if course_code existing in the not_existing_course
            if course_code not in not_existing_course:
                not_existing_course.append(course_code)
        else:
        
            metadata = db.session.query(Metadata).filter_by(YearLevel = year_level, Semester = semester, Batch = batch, CourseId = course.CourseId).first()
            
            if metadata:
                # Check if subject is existing
                subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()
                
                if subject:
                    # Check if Curriculum is existing
                    curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Subject.SubjectCode == subject_code, Metadata.YearLevel == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                    if not curriculum_subject_exist:
                        # Create a curriculum
                        new_curriculum = Curriculum(
                            MetadataId=metadata.MetadataId,
                            SubjectId=subject.SubjectId
                        )
                    
                        db.session.add(new_curriculum)
                        # db.session.commit()
                        
                        # Append the list_curriculum_subjects
                        list_curriculum_subjects.append({
                            "MetadataId": metadata.MetadataId,
                            "Course": course_code,
                            "Subject Code": subject_code,
                            "Year": year_level,
                            "Semester": semester,
                            "Batch": batch
                        })
                    else:
                        # Append the list_curriculum_subjects_exist
                        list_curriculum_subjects_exist.append({
                            "MetadataId": metadata.MetadataId,
                            "Course": course_code,
                            "Subject Code": subject_code,
                            "Year": year_level,
                            "Semester": semester,
                            "Batch": batch
                        })
                else:
                    # Append the subject_code that does not exist
                    list_subject_code_not_exist.append({
                        "MetadataId": metadata.MetadataId,
                        "Course": course_code,
                        "Subject Code": subject_code,
                        "Year": year_level,
                        "Semester": semester,
                        "Batch": batch
                    })
            else: # NO META DATA FIELD
                # Check if subject is existing
                subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()   
        
                new_metadata = Metadata(
                    CourseId=course.CourseId,
                    YearLevel=year_level,
                    Semester=semester,
                    Batch=batch
                )
                    
                db.session.add(new_metadata)
                db.session.flush()
                                                    
                if subject:                       
                    curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Subject.SubjectCode == subject_code, Metadata.YearLevel == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                        
                    if not curriculum_subject_exist:
                        # Create a curriculum
                        new_curriculum = Curriculum(
                            MetadataId=new_metadata.MetadataId,
                            SubjectId=subject.SubjectId
                        )
                
                        db.session.add(new_curriculum)
                        # db.session.commit()
                        
                        # Append the list_curriculum_subjects
                        list_curriculum_subjects.append({
                            "MetadataId": new_metadata.MetadataId,
                            "Course": course_code,
                            "Subject Code": subject_code,
                            "Year": year_level,
                            "Semester": semester,
                            "Batch": batch
                        })
                    else:
                        # Append the list_curriculum_subjects_exist
                        list_curriculum_subjects_exist.append({
                            "MetadataId": new_metadata.MetadataId,
                            "Course": course_code,
                            "Subject Code": subject_code,
                            "Year": year_level,
                            "Semester": semester,
                            "Batch": batch
                        })
                else:
                    # Append the subject_code that does not exist
                    list_subject_code_not_exist.append(subject_code)
        
    # Check if any of this is existing list_curriculum_subjects_exist,list_subject_code_not_exist, not_existing_course then trown an error
    if not_existing_course or list_subject_code_not_exist or list_curriculum_subjects_exist:
        db.session.rollback()
        return jsonify({'error': 'Something went wrong. The data could not be processed successfully.', 'error_data': {'course_not_exist': not_existing_course, 'subject_not_exist': list_subject_code_not_exist, 'curriculum_subject_exist': list_curriculum_subjects_exist}}), 500
    else:
        db.session.commit()
        # db.session.rollback()
        return  jsonify({'result': 'Data added successfully', 'data': (list_curriculum_subjects)}), 200
    

def processUpdatingClassSubjectDetails(data):
    try:
        if data:
            # Update all data in the database
            for class_subject in data:

                class_subject_id = class_subject['ClassSubjectId']
                
                # Get the teacher_name, set it to None if 'TeacherName' is not present
                teacher_id = class_subject['TeacherId']
                schedule = class_subject['Schedule']
                
                # If teacher_id update teacher_id only:
                if teacher_id:
                    db.session.query(ClassSubject).filter_by(ClassSubjectId=class_subject_id).update({
                        'TeacherId': teacher_id
                    })
                
                if schedule:
                    db.session.query(ClassSubject).filter_by(ClassSubjectId=class_subject_id).update({
                        'Schedule': schedule
                    })
                    
                if teacher_id and schedule:
                    db.session.query(ClassSubject).filter_by(ClassSubjectId=class_subject_id).update({
                        'TeacherId': teacher_id,
                        'Schedule': schedule
                    })

            # Commit the changes to the database
            db.session.commit()

            # Return success
            return jsonify({'result': 'Data updated successfully'}), 200
        else:
            # Return updating details failed
            return jsonify({'error': 'Updating details failed. No data provided'}), 500
    except Exception as e:
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


def processAddingStudentInSubject(file, class_subject_id):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        list_students_added = []
        list_student_number_not_exist = []
        list_student_subject_exist = []
        list_class_subject_not_exist = []
        # list_student_graduate = []

        class_subject = db.session.query(ClassSubject).filter_by(ClassSubjectId = class_subject_id)
        
        if class_subject:

            for index, row in df.iterrows():
                # find class_subject_id
                
                
                print('class_subject: ', class_subject)
                if class_subject:
                    student_number = row['Student Number']
                    date_enrolled = row['Date Enrolled'].date()
                
                    student = db.session.query(Student).filter_by(StudentNumber = student_number).first()
                
                    if student:
                        student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId = student.StudentId, ClassSubjectId = class_subject_id).first()
                        
                        if student_class_subject_grade:
                            # list_student_subject_exist
                            list_student_subject_exist.append(student_number)
                        else:
                            # Create StudentClassSubjectGrade
                            new_student_class_subject_grade = StudentClassSubjectGrade(
                                StudentId=student.StudentId,
                                ClassSubjectId=class_subject_id,
                                Grade=0,
                                AcademicStatus=1
                            )
                            
                            db.session.add(new_student_class_subject_grade)
                            db.session.commit()
                            
                            dict_student_class_subject_grade = {
                                "StudentNumber": student.StudentNumber,
                                "Name": student.Name,
                                "Email": student.Email,
                                "Grade": new_student_class_subject_grade.Grade
                            }

                            # append the list_students_added
                            list_students_added.append(dict_student_class_subject_grade)
                    else:
                        # list_student_number_not_exist
                        list_student_number_not_exist.append(student_number)
                    
            if (list_student_number_not_exist or list_student_subject_exist) and len(list_students_added) > 0:
                db.session.rollback()
                return jsonify({'warning': 'Some data added successfully', 'error_data': {'student_not_exist': list_student_number_not_exist, 'student_subject_exist': list_student_subject_exist}, 'added': list_students_added}), 500
            elif (list_student_number_not_exist or list_student_subject_exist) and len(list_students_added) == 0:
                db.session.rollback()
                return jsonify({'error': 'Adding the data failed', 'error_data': {'student_not_exist': list_student_number_not_exist, 'student_subject_exist': list_student_subject_exist}}), 500
            else:
                return jsonify({'success': 'Data added successfully', 'data': list_students_added}), 200
        else:
            return jsonify({'error': 'Class Subject does not exist'}), 400
        
    except Exception as e:
        db.session.rollback()
        print(f'An error occurred: {str(e)}')
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
 
def getMetadata():
    try:
        data_metadata = db.session.query(Metadata, Course).join(Course, Course.CourseId == Metadata.CourseId).all()

        list_metadata = []
        if data_metadata:
            for data in data_metadata:
                # Check data.Course.Name, data.Metadata.Batch and data.Metadata.Semester if exist in list_metadata
                if not any(d['Course'] == data.Course.Name and d['Batch'] == data.Metadata.Batch and d['Semester'] == data.Metadata.Semester for d in list_metadata):
                    # Create a dict
                    dict_metadata = {
                        'MetadataId': data.Metadata.MetadataId,
                        'Course': data.Course.Name,
                        'CourseId': data.Course.CourseId,
                        'Semester': data.Metadata.Semester,
                        'Batch': data.Metadata.Batch
                    }

                    # Append the dict to the list_metadata
                    list_metadata.append(dict_metadata)
                
            print('list_metadata: ', list_metadata)
            return jsonify(list_metadata)
        else:
            return jsonify(None)
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))


def finalizedGradesReport(metadata_id):
    print('metadata_id: ', metadata_id)
    try:
        data_metadata = db.session.query(Metadata, Course).join(Course, Course.CourseId == Metadata.CourseId).filter(Metadata.MetadataId == metadata_id).first()
        list_class = []
        print('data_metadata: ', data_metadata)
        if data_metadata:
            # Select class that has the same Batch, Semester and Course
            data_class = db.session.query(Class).filter_by(Batch = data_metadata.Metadata.Batch, Semester = data_metadata.Metadata.Semester, CourseId = data_metadata.Course.CourseId).all()

            # if data class 
            if data_class:
                # for loop the data_class and make a dictionary and append to the list_class
                for class_data in data_class:
                    print("INSIDE HERE")
                    dict_class = {
                        'ClassId': class_data.ClassId,
                        'CourseId': class_data.CourseId,
                        'Year': class_data.Year,
                        'Section': class_data.Section,
                        'Semester': class_data.Semester,
                        'Batch': class_data.Batch
                    }
                    # Append th list_class
                    list_class.append(dict_class)
                
                    print(list_class)
            else:
                return jsonify({"error": "There no class yet"})
            return jsonify({"message": "Hello"})
        else:
            return jsonify(None)
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))
