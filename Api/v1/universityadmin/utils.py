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
            student_date_enrolled = row['Date Enrolled'] # OK
            
            # Check if the student is already exist in the database based on StudentNumber or Email
            student_number_data = db.session.query(Student).filter(
                (Student.StudentNumber == student_number) 
            ).first()
            student_email_data = db.session.query(Student).filter(
                (Student.Email == student_email) 
            ).first()

            if not student_number_data and not student_email_data:
                password = generate_password()
                gender = 1 if student_gender == 'Male' else 2
                
                
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
                
                # Using the course above generate a CourseEnrolled for students
                new_course_enrolled = CourseEnrolled(
                    CourseId=course.CourseId,
                    StudentId=new_student.StudentId,
                    DateEnrolled=student_date_enrolled
                )
                
                # # Add the new course enrolled to the session
                db.session.add(new_course_enrolled)
                # db.session.commit()
                
                msg = Message('Your current PUP Account has been granted.', sender='your_email@example.com',
                            recipients=[str(new_student.Email)])
                # The message body should be the credentials details
                msg.body = f"Your current PUP Account has been granted. \n\n Email: {str(new_student.Email)} \n Password: {str(new_student.Password)} \n\n Please change your password after you log in. \n\n Thank you."
                
                mail.send(msg)
                
                # Append the student data in list data in format of dict
                list_student_data.append({
                    "Student Number": str(student_number),
                    'Name': str(student_name),
                    "Email": str(student_email),
                    "Mobile Number": str(student_mobile),
                    "Gender": gender
                })
             
            else:
                # Append the student nummber
                list_existing_data.append({'StudentNumber':student_number, 'StudentEmail': student_email})
                # Remove all existing db.session
                
        if list_existing_data:
            db.session.rollback()
            return jsonify({'error': 'The following student number or email already exist in the database ', 'existing_data': (list_existing_data)}), 500
        else:        
            db.session.commit()
            return  jsonify({'result': 'Data added successfully', 'data': list_student_data}), 200
            
    except Exception as e:
        return jsonify({'error': 'An error occurred while processing the file'}), 500
    
def processAddingClass(file):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        list_class_data = []
        list_existing_class_data = []
        list_missing_courses = []
        # For example, you can iterate through rows and access columns like this:
        for index, row in df.iterrows():
            course_code = row['Course Code']
            section = int(row['Section'])
            year = int(row['Year'])
            semester = int(row['Semester'])
            batch = int(row['Batch'])      
            
            # Query the course code in course model
            course =  db.session.query(Course).filter(Course.CourseCode == course_code).first()

            if course:
                # Check if year is current year or + 1 only
                current_year = datetime.datetime.now().year
        
                if batch != current_year and batch != current_year + 1:
                    return jsonify({'error': 'Invalid year. Please select the current year or the next year.'}), 400
                
                # Check if course.id, year, section, semester and batch already existing in class
                class_data = db.session.query(Class).filter(
                    Class.CourseId == course.CourseId, Class.Year == year, Class.Section == section, Class.Semester == semester, Class.Batch == batch).first()
          
                # If existing throw an error
                if not class_data:             
                    new_class = Class(
                        CourseId=course.CourseId,
                        Year=year,
                        Section=section,
                        Semester=semester,
                        Batch=batch, 
                        IsGradeFinalized=False
                    )
                    
                    # Just add in session
                    db.session.add(new_class)
                    db.session.flush()
                    
                    
                    
                    # Make a ClassGrade
                    new_class_grade = ClassGrade(
                        ClassId=new_class.ClassId,
                        PresidentsLister=0,
                        DeansLister=0,
                        Grade= 5.00
                    )
                    db.session.add(new_class_grade)
                    
                    # Combine the course_code, year, section to class_name variable
                    class_name = f"{course_code} {year}-{section}"
                    list_class_data.append({'ClassId':new_class.ClassId,'ClassName':class_name,'Batch':batch, 'Course': course.Name, 'Grade': 'N/A'})
                else:
                    list_existing_class_data.append({
                        'CourseCode': course_code,
                        "Year": year,
                        "Section": section,
                        "Batch": batch,
                        "Semester": semester
                    })
            else:
                # check if course_code not existing in list_missing_course
                if course_code not in list_missing_courses:
                    list_missing_courses.append(course_code)
                
        if list_existing_class_data:
            db.session.rollback()
            return jsonify({'error': 'The class already exist in the database', 'existing_data': list_existing_class_data}), 500
        elif list_missing_courses:
            db.session.rollback()
            return jsonify({'error': 'Course Code does not exist in the database', 'missing_course': list_missing_courses}), 400  
        else:
            db.session.commit()
            return jsonify({'result': "Data added successfully", 'data':list_class_data }), 200   
    except Exception as e:
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
        data_class_subject = db.session.query(ClassSubject, ClassSubjectGrade, Subject, Class, Course, Faculty).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).join(ClassSubjectGrade, ClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId).join(Class, Class.ClassId == ClassSubject.ClassId).join(Course, Course.CourseId == Class.CourseId).join(Faculty, Faculty.TeacherId == ClassSubject.TeacherId).filter(ClassSubject.ClassId == class_id).all()
        
        if data_class_subject:
                # For loop the data_student and put it in dictionary
            list_class_subject = []
            for class_subject in data_class_subject:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_subject.Course.CourseCode} {class_subject.Class.Year}-{class_subject.Class.Section}"
                
                dict_class_subject = {
                    "ClassSubjectId": class_subject.ClassSubject.ClassSubjectId,
                    "SubjectCode": class_subject.Subject.SubjectCode,
                    "Section Code": class_name,
                    "Grade": round(class_subject.ClassSubjectGrade.Grade, 2),  # Round to 2 decimal places
                    "Subject": class_subject.Subject.Name,
                    "Teacher": class_subject.Faculty.Name,
                    "Schedule": class_subject.ClassSubject.Schedule,
                    'Batch': class_subject.Class.Batch,
                    
                }
                # # Append the data
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
        data_class_details = db.session.query(ClassSubject).filter(ClassSubject.ClassSubjectId == classSubjectId).first()
        
        # Get the StudentClassSubjectGrade
        if data_class_details:
            data_student_subject_grade = db.session.query(StudentClassSubjectGrade, Student).join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId).filter(StudentClassSubjectGrade.ClassSubjectId == data_class_details.ClassSubjectId).all()
                        
            if data_student_subject_grade:
                list_student_data = []
                    # For loop the data_student and put it in dictionary
                for student_subject_grade in data_student_subject_grade:
                    dict_student_subject_grade = {
                        "StudentNumber": student_subject_grade.Student.StudentNumber,
                        "Name": student_subject_grade.Student.Name,
                        "Email": student_subject_grade.Student.Email,
                        "Grade": round(student_subject_grade.StudentClassSubjectGrade.Grade, 2)
                    }
                    list_student_data.append(dict_student_subject_grade)
                return  jsonify({'data': list_student_data})
            else:
                return None
        else:
            return None
    except Exception as e:
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
    


def processAddingCurriculumSubjects(file):
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
        list_curriculum_subjects = []
        # Add a dict of already existing students
        list_curriculum_subjects_exist = []
        list_subject_code_not_exist = []
        not_existing_course = []
        # Add a dict of already existing students emai
        print("HELLO")
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
                    print("HELLO2")
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
                    print("HELLO3")
                    # Check if subject is existing
                    subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()   
                    print('subject: ', subject)              
                    if subject:                       
                        curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Subject.SubjectCode == subject_code, Metadata.YearLevel == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                        print("curriculum_subject_exist: ", curriculum_subject_exist)
                        if not curriculum_subject_exist:
                            
                            new_metadata = Metadata(
                                CourseId=course.CourseId,
                                YearLevel=year_level,
                                Semester=semester,
                                Batch=batch,
                            )
                            
                            db.session.add(new_metadata)
                            db.session.flush()
                        
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
                        list_subject_code_not_exist.append({
                            "MetadataId": new_metadata.MetadataId,
                            "Course": course_code,
                            "Subject Code": subject_code,
                            "Year": year_level,
                            "Semester": semester,
                            "Batch": batch
                        })
          
        # Check if any of this is existing list_curriculum_subjects_exist,list_subject_code_not_exist, not_existing_course then trown an error
        if not_existing_course or list_subject_code_not_exist or list_curriculum_subjects_exist:
            db.session.rollback()
            return jsonify({'error': 'The following data already exist in the database', 'existing_data': {'course': not_existing_course, 'subject': list_subject_code_not_exist, 'curriculum': list_curriculum_subjects_exist}}), 500
        else:
            db.session.commit()
            # db.session.rollback()
            return  jsonify({'result': 'Data added successfully', 'data': (list_curriculum_subjects)}), 200
        
            
    except Exception as e:
        return jsonify({'error': 'An error occurred while processing the file'}), 500
    
    #     # Now you can access and manipulate the data in the DataFrame
    #     # For example, you can iterate through rows and access columns like this:
    #     for index, row in df.iterrows():
    #         # Extract the values from the DataFrame
    #         student_number = row['Student Number'] # OK
    #         student_name = row['Student Name']
    #         section_code = row['Section Code']
    #         subject_code = row['SubjectCode'] # OK
    #         semester = row['Semester'] # OK
    #         grade = row['Grade']
    #         batch = row['Batch'] # OK
            
    #         # Split the section_code by the last space and keep the first part
    #         course_code = section_code.rsplit(' ', 1)[0] 
            
    #         # Split the section_code by space, get the last part, and split it by hyphen '-' to extract year and section
    #         year, section = section_code.split(' ')[-1].split('-')

    #         # Now you can use the modified_section_code as needed in your code
    #         student_data = (
    #             db.session.query(Student,  StudentClassSubjectGrade, ClassSubject, Class, Subject, Course)
    #             .join(StudentClassSubjectGrade, StudentClassSubjectGrade.StudentId == Student.StudentId)
    #             .join(ClassSubject, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId)
    #             .join(Class, Class.ClassId == ClassSubject.ClassId)
    #             .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
    #             .join(Course, Course.CourseId == Class.CourseId)
    #             .filter(Student.StudentNumber == student_number, Class.Year == year, Class.Section == section, Class.Batch == batch, Class.Semester == semester,  Subject.SubjectCode == subject_code)
    #             .order_by(desc(Student.Name), desc(Class.Year), desc(Class.Section), desc(Class.Batch))
    #             .first()
    #         )
            
            
    #         if(student_data.Class.IsGradeFinalized==False):
    #             # Update the Class isGradeFinalized to False
    #             student_data.StudentClassSubjectGrade.Grade = grade
                
    #             # Save only but dont commit in database
    #             db.session.add(student_data.StudentClassSubjectGrade)
    #         else:
    #             return jsonify({'error': 'The grade has been finalized. Contact admin if there is an issue exist'}), 500
    #     # If all data is updated successfully then commit the data
    #     db.session.commit()
    #     return jsonify({'success': 'File uploaded and data processed successfully'}), 200

    # except Exception as e:
    #     return jsonify({'error': 'An error occurred while processing the file'}), 500