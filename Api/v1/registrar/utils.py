from models import StudentClassGrade, ClassGrade, Class, Course, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, db, UniversityAdmin, Metadata, Registrar, Student, StudentRequirements, LatestBatchSemester, ClassSubjectGrade
from sqlalchemy import desc, distinct, func, and_
import re
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict

from datetime import date, datetime

from sklearn.linear_model import LinearRegression
from flask import session, jsonify
from static.js.utils import convertGradeToPercentage, checkStatus
from flask_mail import Message
from mail import mail
import pandas as pd
import random
import string
from sqlalchemy.orm import Session

import numpy as np
from collections import defaultdict
import math


def getCurrentUser():
    current_user_id = session.get('user_id')
    return Registrar.query.get(current_user_id)


def is_valid_email(email):
    # Regular expression for a basic email validation
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_pattern, email)


def is_valid_phone_number(phone_number):
    # Regular expression for a phone number validation
    phone_pattern = r'^09\d{9}$'
    return re.match(phone_pattern, phone_number)


def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password
    

def getRegistrarData(str_registrar_id):
    try:
        data_university_admin = (
            db.session.query(Registrar).filter(
                Registrar.RegistrarId == str_registrar_id).first()
        )

        if data_university_admin:
          

            dict_student_data = {
                "UnivAdminNumber": data_university_admin.RegistrarNumber,
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


def updateRegistrarData(str_registrar_id, number, residentialAddress):
    try:
        number = re.sub(r'\D', '', number)  # Remove non-digit characters
        number_pattern = re.compile(r'^09\d{9}$')

        if not number_pattern.match(number):
            return {"type": "mobile", "status": 400}

        if residentialAddress is None or residentialAddress.strip() == "":
            return {"type": "residential", "status": 400}

        # Update the student data in the database
        data_registrar = db.session.query(Registrar).filter(Registrar.RegistrarId == str_registrar_id).first()
        
        if data_registrar:
            data_registrar.MobileNumber = number
            data_registrar.ResidentialAddress = residentialAddress
            db.session.commit()
                        
            return {"message": "Data updated successfully", "number": number, "residentialAddress": residentialAddress, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}


def updatePassword(str_registrar_id, password, new_password, confirm_password):
    try:
        data_registrar = db.session.query(Registrar).filter(Registrar.RegistrarId == str_registrar_id).first()

  
        password_validator = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$'

        error = False
        errorList = []
        if not password:
            error = True
            errorList.append({'type': 'current_password', 'message': "Password must not be invalid"})
        elif len(password) < 8:
            error = True
            errorList.append({'type': 'current_password', 'message': "Password must be 8 characters long"})
        elif not re.match(password_validator, password):
            error = True
            errorList.append({'type': 'current_password', 'message': "Password must contain a number and characters uppercase and lowercase"})

        if not new_password:
            error = True
            errorList.append({'type': 'new_password', 'message': "New Password must not be invalid"})
        elif len(new_password) < 8:
            error = True
            errorList.append({'type': 'new_password', 'message': "New Password must be 8 characters long"})
        elif not re.match(password_validator, new_password):
            error = True
            errorList.append({'type': 'new_password', 'message': "New Password must contain a number and characters uppercase and lowercase"})

        if not confirm_password:
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must not be invalid"})
        elif len(confirm_password) < 8:
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must be 8 characters long"})
        elif not re.match(password_validator, confirm_password):
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must contain a number and characters uppercase and lowercase"})

        if new_password != confirm_password:
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must match with New Password"})

        if error:
            return {"error": True, 'errorList': errorList, "status": 400}
            
        
        if data_registrar:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_registrar.Password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(new_password)
                data_registrar.Password = new_hashed_password
                db.session.commit()
                return {"message": "Password changed successfully", "status": 200}

            else:
                return {"message": "Changing Password was unsuccessful. Please try again.", "status": 401}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}

def getStatistics():
    try:
        # Get the teacher active in Faculty
        teacher_active_count = db.session.query(Faculty).filter_by(Status = "Active").count()
        
        # Get count of student enrolled in courses with the current year
        # Get the current year
        current_year = datetime.now().year
        # Get the count of student enrolled in courses based on DateEnrolled from last date
        student_enrolled_count = db.session.query(CourseEnrolled).filter(CourseEnrolled.DateEnrolled >= f'{current_year}-01-01').count()
        
        # Check if student enrolled if not then - 1 with current year
        if student_enrolled_count == 0:
            student_enrolled_count = db.session.query(CourseEnrolled).filter(CourseEnrolled.DateEnrolled >= f'{current_year - 1}-01-01').count()
        
        # Get the class
        class_data_count = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Batch == current_year).count()
        
        # Check if class data
        if class_data_count == 0:
            class_data_count = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Batch == current_year - 1).count()
        # Return all elements
        return jsonify({ 
            'success': True, 
            'result':{
                'teacher_active_count': teacher_active_count,
                'student_enrolled_count': student_enrolled_count,
                'class_data_count': class_data_count
            }
        })
        
    except Exception as e:
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
    

def predict_next_years(data_list, list_course, years_to_predict=3):
    years = np.array(data_list['Year']).reshape(-1, 1)
    
    predictions = {'Year': []}
    for course in list_course:
        predictions[course] = []
    
    future_years = [max(data_list['Year']) + i for i in range(1, years_to_predict + 1)]

    for key in list_course:
        values = np.array(data_list[key])
        model = LinearRegression()
        model.fit(years, values)
        future_values = model.predict(np.array(future_years).reshape(-1, 1))
        predictions[key] = future_values.tolist()
    
    predictions['Year'] = future_years
    return predictions

def getEnrollmentTrends(startYear, endYear):
    try:
        # Query data with required fields
        data_course_enrolled = db.session.query(
            Course.CourseCode, CourseEnrolled.DateEnrolled
        ).join(Course, Course.CourseId == CourseEnrolled.CourseId).order_by(CourseEnrolled.DateEnrolled).all()

        if data_course_enrolled:
            # Create a dictionary to store year-wise course counts
            course_year_counts = defaultdict(lambda: defaultdict(int))
            list_course = []
            
            # Iterate through the data to calculate counts
            for course_code, date_enrolled in data_course_enrolled:
                # Check if course code existing in list course if not add to the list
                if course_code not in list_course:
                    list_course.append(course_code)
                
                year_enrolled = date_enrolled.year
                course_year_counts[year_enrolled][course_code] += 1

            # Convert the counts to a list of dictionaries with the desired format
            trend_data = []

            data_list = {"Year": []}
            latest_year = 0
            # Find lowest, highest, and total enrollment counts
            for year, course_counts in course_year_counts.items():
                if year > latest_year:
                    latest_year = year
                trend_item = {"x": year, **course_counts}
                trend_data.append(trend_item)
                data_list["Year"].append(year)
            
            # Loop to list_course
            for course in list_course:
                data_list[course] = []
            
            # Loop to the trend data
            for trend in trend_data:
                # Loop to list_course
                for course in list_course:
                    # Check if course is in trend
                    if course in trend:
                        data_list[course].append(trend[course])
                    else:
                        data_list[course].append(0)
                
            # Return the data
            predict_length = endYear -latest_year
            future_results = predict_next_years(data_list, list_course, predict_length)
            # Loop through the predicted results and filter for the specified years
            predicted_year_results = []
            for i, year in enumerate(future_results['Year']):
                predicted_year_data = {'Year': year}
                if year >= startYear and year <= endYear:
                    for course in list_course:
                        course_enrolled = max(math.ceil(future_results[course][i]), 0)
                        predicted_year_data[course] = course_enrolled
                    predicted_year_results.append(predicted_year_data)
                  
            predicted_year_results.sort(key=lambda x: x['Year'])

            return jsonify({'success': True, 'course_list': list_course, 'enrollment_trends': predicted_year_results})
          
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None



def getOverallCoursePerformance():
    try:
        data_course_grade = db.session.query(
            Course.CourseId,
            Course.CourseCode,
            CourseGrade.Batch,
            func.avg(CourseGrade.Grade).label('average_grade')
        ).join(
            Course, Course.CourseId == CourseGrade.CourseId
        ).group_by(
            Course.CourseId, CourseGrade.Batch
        ).order_by(
            CourseGrade.Batch, Course.CourseId
        ).all()

        list_course = []

        if data_course_grade:
            course_year_grades = defaultdict(dict)

            for course_grade in data_course_grade:
                course_code = course_grade.CourseCode
                year = course_grade.Batch
                course_id = course_grade.CourseId
                
                # Check if course_code is not in list_course
                if course_code not in list_course:
                    list_course.append(course_code)

                grade = round(convertGradeToPercentage(course_grade.average_grade), 2)

                if year not in course_year_grades:
                    course_year_grades[year] = {"x": year}

                course_year_grades[year][course_code] = grade

            # Convert the data into a list of dictionaries
            formatted_data = list(course_year_grades.values())
            return jsonify({'success': True, 'list_course': list_course, 'course_performance': formatted_data})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return e
    

def getStudentData(skip, top, order_by, filter):
    try:
        student_query = (
            db.session.query(CourseEnrolled, Student, Course).join(Student, Student.StudentId == CourseEnrolled.StudentId).join(Course, Course.CourseId == CourseEnrolled.CourseId)
        )
        
        filter_conditions = []
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split("),'")[0]
                    value = part.split("'")[1]
                    column_str = None
                    if column_name.strip() == 'StudentNumber':
                        column_str = getattr(Student, 'StudentNumber')
                    elif column_name.strip() == 'LastName':
                        column_str = getattr(Student, 'LastName')
                    elif column_name.strip() == 'FirstName':
                        column_str = getattr(Student, 'FirstName')
                    elif column_name.strip() == 'MiddleName':
                        column_str = getattr(Student, 'MiddleName')
                    elif column_name.strip() == 'Email':
                        column_str =  getattr(Student, 'Email')     
                    elif column_name.strip() == 'MobileNumber':
                        column_str = getattr(Student, 'MobileNumber')
                    elif column_name.strip() == 'Program':
                        column_str = getattr(Course, 'CourseCode')
                    elif column_name.strip() == 'DateEnrolled':
                        column_str = getattr(CourseEnrolled, 'DateEnrolled')
                        filter_conditions.append(
                            CourseEnrolled.DateEnrolled == (1 if value == 'male' else 2)
                        )
                    elif column_name.strip() == 'Gender':
                        filter_conditions.append(
                            Student.Gender == (1 if value == 'male' else 2)
                        )
                        continue
                    
                    if column_str:
                        # Append column_str
                        filter_conditions.append(
                            func.lower(column_str).like(f'%{value}%')
                        )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    
                    column_num = None
                    int_value = value.strip(')')
             
                    if column_name.strip() == 'Batch':
                        column_num = CourseEnrolled.CurriculumYear
                    if column_name.strip() == 'Status':
                        column_num = CourseEnrolled.Status
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                        
        filter_query = student_query.filter(and_(*filter_conditions))
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Student, 'StudentNumber')
            elif order_by.split(' ')[0] == "LastName":
                order_attr = getattr(Student, 'LastName')
            elif order_by.split(' ')[0] == "FirstName":
                order_attr = getattr(Student, 'FirstName')
            elif order_by.split(' ')[0] == "MiddleName":
                order_attr = getattr(Student, 'MiddleName')
            elif order_by.split(' ')[0] == 'Email':
                order_attr = getattr(Student, 'Email')
            elif order_by.split(' ')[0] == 'Gender':
                order_attr = getattr(Student, 'Gender')
            elif order_by.split(' ')[0] == 'MobileNumber':
                order_attr = getattr(Student, 'MobileNumber')
            elif order_by.split(' ')[0] == 'Program':
                order_attr = getattr(Course, 'CourseCode')
            elif order_by.split(' ')[0] == 'DateEnrolled':
                order_attr = getattr(CourseEnrolled, 'DateEnrolled')
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(CourseEnrolled, 'CurriculumYear')
            elif order_by.split(' ')[0] == 'Status':
                order_attr = getattr(CourseEnrolled, 'Status')
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(CourseEnrolled.CurriculumYear), desc(Course.CourseCode), desc(Student.StudentNumber))
        
        
        # Query for counting all records
        total_count = order_query.count()
        # Limitized query = 
        student_limit_offset_query = order_query.offset(skip).limit(top).all()
        if student_limit_offset_query:
             # For loop the student_query and put it in dictionary
            list_student_data = []
            for data in student_limit_offset_query:
                status = "Regular" if data.CourseEnrolled.Status == 0 else "Graduated" if data.CourseEnrolled.Status == 1 else "Irregular" if data.CourseEnrolled.Status == 2 else "Drop"
                dict_student = {
                    "StudentId": data.Student.StudentId,
                    "StudentNumber": data.Student.StudentNumber,
                    "LastName": data.Student.LastName,
                    "FirstName": data.Student.FirstName,
                    "MiddleName": data.Student.MiddleName,
                    "Email": data.Student.Email,
                    "MobileNumber": data.Student.MobileNumber,
                    "Gender": "Male" if data.Student.Gender == 1 else "Female",
                    "Program": data.Course.CourseCode,
                    "DateEnrolled": data.CourseEnrolled.DateEnrolled.strftime('%Y-%m-%d'),
                    "Batch": data.CourseEnrolled.CurriculumYear,
                    "Status": status
                }
                # Append the data
                list_student_data.append(dict_student)
            return jsonify({"result": list_student_data, "count":total_count})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None
    

def processAddingStudents(data, excelType=False):
    try:
        def errorObject(data):
            return ({
                        'StudentNumber': data[0],
                        'LastName': data[1],
                        'FirstName': data[2],
                        'MiddleName': data[3],
                        'Email': data[4],
                        'Phone': data[5],
                        'Address': data[6],
                        'Gender': data[7],
                        'Program': data[8],
                        'DateEnrolled': data[9],  # Adding the original string for reference
                        'Batch': data[10],
                        'Error': data[11]
                    })
        
        if excelType == True:
            # Check if the file is empty
            if data.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            # Check file extension
            if not data.filename.endswith(('.xlsx', '.xls')):
                return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400


            # Read the Excel file into a DataFrame
            df = pd.read_excel(data)
            
            # dict data list
            list_student_data = []
            errors = []
            
            for index, row in df.iterrows():
                student_number = row['Student Number'] # OK
                student_lastname = row['LastName']
                student_firstname = row['FirstName']
                student_middlename = row['MiddleName']
                student_email = row['Email']
                student_mobile =  str(row['Phone Number'])
                student_address = row['Address'] # OK
                student_gender = row['Gender'] # OK
                student_program = row['Program']
                student_date_enrolled = row['Date Enrolled']
                student_batch = row['Batch'] # OK
                student_status = 2 if row.get('Status') == "Irregular" else 0


                if student_mobile:
                    # Check for length of phone number if 10 add 0 in first
                    if len(student_mobile) == 10:
                        student_mobile = '0' + student_mobile
                    elif len(student_mobile) != 11:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Mobile Format']))
                        continue
                    
            
                # Check if Date Enrolled is a valid date format
                if student_date_enrolled is not None:
                    # Check if it is in date format then convert it into YYYY-MM-DD
                    if isinstance(student_date_enrolled, datetime):
                        student_date_enrolled = student_date_enrolled.strftime("%Y-%m-%d")
                    else:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Date Enrolled format']))
                        continue
                else:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Date Enrolled']))
                    continue
                
                # Check if Batch is a valid format (e.g., numeric)
                if not str(student_batch).isdigit():
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Batch format']))
                    continue
                
                elif not student_batch:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Batch']))
                    continue
                
                # Check if Email is a valid format
                if not is_valid_email(student_email):
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Email format']))
                    continue
                elif not student_email:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender  , student_program, student_date_enrolled, student_batch, 'Invalid Email format']))
                    continue
                
                # Check if Phone Number is a valid format
                if student_mobile and not is_valid_phone_number(student_mobile):
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Phone Number format']))
                    continue
            
                if not student_program:
                    errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Invalid Program']))
                    continue
                
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

                    course = db.session.query(Course).filter_by(CourseCode=student_program).first()

                    # Add the new student in the database

                    # Ensure the mobile number has a leading zero
                    if not student_mobile.startswith('0'):
                        student_mobile = '0' + student_mobile

                    new_student = Student(
                        StudentNumber=student_number,
                        LastName=student_lastname,
                        FirstName=student_firstname,
                        MiddleName=student_middlename,
                        Email=student_email,
                        MobileNumber=str(student_mobile),
                        ResidentialAddress=student_address,
                        Gender=gender,
                        Password=generate_password_hash(password)
                    )


                    db.session.add(new_student)
                    db.session.flush()
                    
                    new_course_enrolled = CourseEnrolled(
                        CourseId=course.CourseId,
                        StudentId=new_student.StudentId,
                        DateEnrolled=student_date_enrolled,
                        Status=student_status,
                        CurriculumYear=student_batch
                    )
                    
                    new_student_requirements = StudentRequirements(
                        StudentId=new_student.StudentId,
                    )
                    
                    # # Add the new course enrolled to the session
                    db.session.add(new_course_enrolled)
                    db.session.add(new_student_requirements)
                    db.session.commit()
                    
                    msg = Message('Your current PUP Account has been granted.', sender='your_email@example.com',
                                recipients=[str(new_student.Email)])
                    # The message body should be the credentials details
                    msg.body = f"Your current PUP Account has been granted. \n\n Email: {str(new_student.Email)} \n Password: {str(password)} \n\n Please change your password after you log in. \n\n Thank you."
                    
                    mail.send(msg)
                    
                    if not gender:
                        list_student_data.append({
                            "Email": str(student_email),
                            "Gender": "N/A",
                            "Mobile Number": str(student_mobile),
                            'LastName': student_lastname,
                            'FirstName': student_firstname,
                            'MiddleName': student_middlename,
                            "Student Number": str(student_number)
                        })
                    else:
                        list_student_data.append({
                            "Email": str(student_email),
                            "Gender": student_gender,
                            "Mobile Number": str(student_mobile),
                            'LastName': student_lastname,
                            'FirstName': student_firstname,
                            'MiddleName': student_middlename,
                            "Student Number": str(student_number)
                        })
                else:
                    if student_number_data:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Student Number already exist']))
                    else:
                        errors.append(errorObject([student_number, student_lastname, student_firstname, student_middlename, student_email, student_mobile, student_address, student_gender, student_program, student_date_enrolled, student_batch, 'Email already exist']))
                    
            if errors and list_student_data:
                db.session.rollback()
                return jsonify({'warning': 'Some data cannot be added.', 'errors': errors, 'data': list_student_data}), 500
            if errors and not list_student_data:
                db.session.rollback()
                return jsonify({'error': 'Adding data failed.', 'errors': errors}), 500
            else:        
                return  jsonify({'result': 'Data added successfully', 'data': list_student_data}), 200
        else:
            if data:
                student_number = data['StudentNumber'].strip()
                student_lastname = data['LastName']
                student_firstname = data['FirstName']
                student_middlename = data.get('MiddleName', '')
                student_email = data['Email'].strip()
                student_gender = data.get('Gender', 1) # OK
                student_mobile =  str(data['MobileNumber']).strip()
                student_program = data['Program'].strip()
                student_date_enrolled = data['DateEnrolled']
                student_batch = data['Batch'] # OK
                student_status = 0 if data['Status'] == "Regular" else 2
                
                if student_mobile:
                    # Check for length of phone number if 10 add 0 in first
                    if len(student_mobile) == 10:
                        student_mobile = '0' + student_mobile
                    
            
                # Convert student_date_enrolled to date format
                if student_date_enrolled is not None:
                    try:
                        # Adjust the format string to include the time component
                        student_date_enrolled = datetime.strptime(student_date_enrolled, "%Y-%m-%dT%H:%M:%S.%fZ")
                        
                        # Extract only the date part
                        student_date_enrolled = student_date_enrolled.date()
                        
                    except Exception as e:
                        return jsonify({'error': 'Invalid Date Enrolled format'}), 400
              
                # Check if Batch is a valid format (e.g., numeric)
                if not type(student_batch) == int:
                    return jsonify({'error': 'Invalid Batch format'}), 400
                
                # Check if Email is a valid format
                if not is_valid_email(student_email):
                    return jsonify({'error': 'Invalid Email format'}), 400
                # Check if Phone Number is a valid format
                if student_mobile and not is_valid_phone_number(student_mobile):
                    return jsonify({'error': 'Invalid Phone Number format'}), 400

                
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

                    course = db.session.query(Course).filter_by(CourseCode=student_program).first()
                    
                    
                # Add the new student in the database

                    # Ensure the mobile number has a leading zero
                    if not student_mobile.startswith('0'):
                        student_mobile = '0' + student_mobile
                    
                    new_student = Student(
                        StudentNumber=student_number,
                        LastName=student_lastname,
                        FirstName=student_firstname,
                        MiddleName=str(student_middlename),
                        Email=student_email,
                        MobileNumber=str(student_mobile),
                        Gender=gender,
                        Password=generate_password_hash(password)
                    )
                    
                    db.session.add(new_student)
                    db.session.flush()
                    new_course_enrolled = CourseEnrolled(
                        CourseId=course.CourseId,
                        StudentId=new_student.StudentId,
                        DateEnrolled=student_date_enrolled,
                        Status=student_status,
                        CurriculumYear=student_batch
                    )
                    
                    new_student_requirements = StudentRequirements(
                        StudentId=new_student.StudentId,
                    )
                    # # Add the new course enrolled to the session
                    db.session.add(new_course_enrolled)
                    db.session.add(new_student_requirements)
                    db.session.commit()
                    
                    msg = Message('Your current PUP Account has been granted.', sender='your_email@example.com',
                                recipients=[str(new_student.Email)])
                    # The message body should be the credentials details
                    msg.body = f"Your current PUP Account has been granted. \n\n Email: {str(new_student.Email)} \n Password: {str(password)} \n\n Please change your password after you log in. \n\n Thank you."
                    
                    mail.send(msg)
                    # Return data added success
                    
                    return jsonify({'result': 'Data added successfully'}), 200
                    
                else:
                    if student_number_data:
                        return jsonify({'error': 'Student Number already exist'}), 400
                    else:
                        # Return email already exist
                        return jsonify({'error': 'Email already exist'}), 400
    except Exception as e:
        db.session.rollback()
        print("ERROR: ", e)
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
    

def deleteStudentData(studentId):
    try:
      # Find student
        student_data = db.session.query(Student).filter_by(StudentId = studentId).first()
        if student_data:
            # Check if student existing in one of the class subject grade
            student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId = studentId).first()
            if student_class_subject_grade:
                return jsonify({'error': 'Student cannot be deleted because it is existing in the class already'}), 400
            else:
                db.session.delete(student_data)
                db.session.commit()
                return jsonify({'result': 'Data deleted successfully'}), 200
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e}), 500
    

def getStudentAddOptions():
    try:
      # Make gender options
        genderOptionList = [{"Gender":"Male"}, {"Gender":"Female"}]
        # Make course options
        courseOptionList = []
        course_data = db.session.query(Course).all()
        if course_data:
            for course in course_data:
                courseOptionList.append({"Program": course.CourseCode})
        
        # Make batch options for prev year, current year and future year. For example 2024 is current year then it should be 2023, 2024, 2025
        
        
        current_year = datetime.now().year
        batchOptionList = [{"Batch": current_year+1}, {"Batch": current_year},{"Batch": current_year-1}]
        
        return jsonify({'result':{"genderOptions": genderOptionList, "courseOptions": courseOptionList, "batchOptions": batchOptionList}})
        
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e})


from sqlalchemy import and_

def getStudentRequirements(skip, top, order_by, filter):
    try:
        # Fetch required columns only
        student_requirements_query = db.session.query(Student.StudentId, Student.StudentNumber, Student.LastName, Student.FirstName, Student.MiddleName,
                                                       StudentRequirements.F_137, StudentRequirements.F_138, StudentRequirements.GoodMoralSeal,
                                                       StudentRequirements.Grade12, StudentRequirements.Grade11, StudentRequirements.SARForm,
                                                       StudentRequirements.PSA, StudentRequirements.Diploma, StudentRequirements.Grade10WithoutSeal, StudentRequirements.IsCompleted)\
                                                .join(Student, Student.StudentId == StudentRequirements.StudentId)
        filter_conditions = []
        
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Check if part contains startswith
                    if 'startswith(' in part:
                        
                        # Extracting column name and value
                        column_name = part.split("(")[3].split("),'")[0]
                        value = part.split("'")[1]
                        column_str = None
                    else:
                        # Extracting column name and value
                        column_name = part.split("(")[2].split(")")[0]
                        value = part.split("'")[1]
                        column_str = None
                    if column_name.strip() == 'StudentNumber':
                        column_str = getattr(Student, 'StudentNumber')
                    elif column_name.strip() == 'LastName':
                        column_str = getattr(Student, 'LastName')
                    elif column_name.strip() == 'FirstName':
                        column_str = getattr(Student, 'FirstName')
                    elif column_name.strip() == 'MiddleName':
                        column_str = getattr(Student, 'MiddleName')
                    # Check if the column is F_137 then make a check for its value
                    elif column_name.strip() == 'F_137':
                        filter_conditions.append(
                            StudentRequirements.F_137 == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'F_138':
                        filter_conditions.append(
                            StudentRequirements.F_138 == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'GoodMoralSeal':
                        filter_conditions.append(
                            StudentRequirements.GoodMoralSeal == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'Grade12':
                        filter_conditions.append(
                            StudentRequirements.Grade12 == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'Grade11':
                        filter_conditions.append(
                            StudentRequirements.Grade11 == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'SARForm':
                        filter_conditions.append(
                            StudentRequirements.SARForm == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'PSA':
                        filter_conditions.append(
                            StudentRequirements.PSA == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'Diploma':
                        filter_conditions.append(
                            StudentRequirements.Diploma == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'Grade10WithoutSeal':
                        filter_conditions.append(
                            StudentRequirements.Grade10WithoutSeal == (True if value == 'submitted' else False)
                        )
                        continue
                    elif column_name.strip() == 'Completed':
                        filter_conditions.append(
                            StudentRequirements.IsCompleted == (True if value == 'completed' else False)
                        )
                        continue
                 
                    if column_str:
                        # Append column_str
                        filter_conditions.append(
                            func.lower(column_str).like(f'%{value}%')
                        )
                else:   
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    column_num = None
                    int_value = value.strip(')')
                    
                    # Check for column name 
                    if column_name.strip() == 'Batch':
                        column_num = Metadata.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = Metadata.Semester
               
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
        # Apply all filter conditions with 'and'
        filter_query = student_requirements_query.filter(and_(*filter_conditions))

         # Apply sorting logic
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Student, 'StudentNumber')
            elif order_by.split(' ')[0] == "LastName":
                order_attr = getattr(Student, "LastName")
            elif order_by.split(' ')[0] == "FirstName":
                order_attr = getattr(Student, "FirstName")
            elif order_by.split(' ')[0] == "MiddleName":
                order_attr = getattr(Student, "MiddleName")
            elif order_by.split(' ')[0] == "F_137":
                order_attr = getattr(StudentRequirements, "F_137")
            elif order_by.split(' ')[0] == "F_138":
                order_attr = getattr(StudentRequirements, "F_138")
            elif order_by.split(' ')[0] == "GoodMoralSeal":
                order_attr = getattr(StudentRequirements, "GoodMoralSeal")
            elif order_by.split(' ')[0] == "Grade12":
                order_attr = getattr(StudentRequirements, "Grade12")
            elif order_by.split(' ')[0] == "Grade11":
                order_attr = getattr(StudentRequirements, "Grade11")
            elif order_by.split(' ')[0] == "SARForm":
                order_attr = getattr(StudentRequirements, "SARForm")
            elif order_by.split(' ')[0] == "Diploma":
                order_attr = getattr(StudentRequirements, "Diploma")
            elif order_by.split(' ')[0] == "PSA":
                order_attr = getattr(StudentRequirements, "PSA")
            elif order_by.split(' ')[0] == "Grade10WithoutSeal":
                order_attr = getattr(StudentRequirements, "Grade10WithoutSeal")
            elif order_by.split(' ')[0] == "Completed":
                order_attr = getattr(StudentRequirements, "IsCompleted")

            if order_attr:
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Student.StudentNumber))
        
        total_count = order_query.count()
        student_requirements_main_query = order_query.offset(skip).limit(top).all()

        if student_requirements_main_query:
            list_student_requirements = []
            for data in student_requirements_main_query:
                student_data = {
                    "StudentId": data[0],
                    "StudentNumber": data[1],
                    "LastName": data[2],
                    "FirstName": data[3],
                    "MiddleName": data[4],
                    'F_137': 'Submitted' if data[5] else "Missing",
                    'F_138': 'Submitted' if data[6] else "Missing",
                    'GoodMoralSeal': 'Submitted' if data[7] else "Missing",
                    'Grade12': 'Submitted' if data[8] else "Missing",
                    'Grade11': 'Submitted' if data[9] else "Missing",
                    'SARForm': 'Submitted' if data[10] else "Missing",
                    'PSA': 'Submitted' if data[11] else "Missing",
                    'Diploma': 'Submitted' if data[12] else "Missing",
                    'Grade10WithoutSeal': 'Submitted' if data[13] else "Missing",
                    'Completed': "Completed" if data[14] == True else "Incomplete"
                }
                list_student_requirements.append(student_data)
                
            return jsonify({"result": list_student_requirements, 'count': total_count})

    except Exception as e:
        print("ERROR: ", e)
        # Handle exceptions
        return jsonify({"error": str(e)})
    
def processUpdatingStudentRequirements(file):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        submitted_data = False
        errors = []
        
        for index, row in df.iterrows():
            student_number = row['Student Number'].strip() if isinstance(row['Student Number'], str) else row['Student Number']
            f_137 = row['F-137'].strip() if isinstance(row['F-137'], str) else row['F-137']
            f_138 = row['F-138'].strip() if isinstance(row['F-138'], str) else row['F-138']
            good_moral = row['GoodMoralSeal'].strip() if isinstance(row['GoodMoralSeal'], str) else row['GoodMoralSeal']
            grade_12 = row['Grade12'].strip() if isinstance(row['Grade12'], str) else row['Grade12']
            grade_11 = row['Grade11'].strip() if isinstance(row['Grade11'], str) else row['Grade11']
            sar_form = row['SARForm'].strip() if isinstance(row['SARForm'], str) else row['SARForm']
            psa = row['PSA'].strip() if isinstance(row['PSA'], str) else row['PSA']
            diploma = row['Diploma'].strip() if isinstance(row['Diploma'], str) else row['Diploma']
            grade_10_without_seal = row['Grade10WithoutSeal'].strip() if isinstance(row['Grade10WithoutSeal'], str) else row['Grade10WithoutSeal']
            
            # Get student and student requirements
            student = db.session.query(Student, StudentRequirements).join(StudentRequirements, StudentRequirements.StudentId == Student.StudentId).filter(Student.StudentNumber == str(student_number.strip())).first()
            
            # Update the StudentRequirements
            if student:
                student.StudentRequirements.F_137 = True if f_137.lower() == 'submitted' else False
                student.StudentRequirements.F_138 = True if f_138.lower() == 'submitted' else False
                student.StudentRequirements.GoodMoralSeal = True if good_moral.lower() == 'submitted' else False
                student.StudentRequirements.Grade12 = True if grade_12.lower() == 'submitted' else False
                student.StudentRequirements.Grade11 = True if grade_11.lower() == 'submitted' else False
                student.StudentRequirements.SARForm = True if sar_form.lower() == 'submitted' else False
                student.StudentRequirements.PSA = True if psa.lower() == 'submitted' else False
                student.StudentRequirements.Diploma = True if diploma.lower() == 'submitted' else False
                student.StudentRequirements.Grade10WithoutSeal = True if grade_10_without_seal.lower() == 'submitted' else False
                submitted_data = True
            else:
                errors.append({
                    'StudentNumber': student_number,
                    'F_137': f_137,
                    'F_138': f_138,
                    'GoodMoralSeal': good_moral,
                    'Grade12': grade_12,
                    'Grade11': grade_11,
                    'SARForm': sar_form,
                    'PSA': psa,
                    'Diploma': diploma,
                    'Grade10WithoutSeal': grade_10_without_seal,
                    'Error': 'Student not found'
                })
                
        # Check if errors and submitted data
        if errors and submitted_data:
            db.session.commit()
            return jsonify({'warning': 'Some data cannot be updated.', 'errors': errors}), 400
        if errors and not submitted_data:
            db.session.commit()
            return jsonify({'error': 'Updating data failed.', 'errors': errors}), 400
        else:
            db.session.commit()
            return jsonify({'result': 'Data updated successfully'}), 200
        
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
    

    


def get_lister_counts(item):
    president_lister_count = db.session.query(func.count(StudentClassGrade.Lister)).\
        join(Class, Class.ClassId == StudentClassGrade.ClassId).\
        join(Metadata, Metadata.MetadataId == Class.MetadataId).\
        filter(Metadata.Batch == item.Batch, StudentClassGrade.Lister == 1).\
        scalar()

    dean_lister_count = db.session.query(func.count(StudentClassGrade.Lister)).\
        join(Class, Class.ClassId == StudentClassGrade.ClassId).\
        join(Metadata, Metadata.MetadataId == Class.MetadataId).\
        filter(Metadata.Batch == item.Batch, StudentClassGrade.Lister == 2).\
        scalar()

    return president_lister_count, dean_lister_count

def get_list_lister_data(data_latest_batch_semester):
    list_lister_data = []
    max_count = 0
    min_count = None

    if data_latest_batch_semester:
        for item in data_latest_batch_semester:
            president_lister_count, dean_lister_count = get_lister_counts(item)

            max_count = max(max_count, president_lister_count, dean_lister_count)
            if not min_count:
                min_count = min(president_lister_count, dean_lister_count)
            else:
                min_count = min(min_count, president_lister_count, dean_lister_count)

            grade_dict = {"year": str(item.Batch), "president": president_lister_count, "dean": dean_lister_count}
            list_lister_data.append(grade_dict)

        return list_lister_data, max_count, min_count

    return None, None, None

def getListerTrends():
    try:
        data_latest_batch_semester_desc = db.session.query(LatestBatchSemester).distinct(LatestBatchSemester.Batch).order_by(desc(LatestBatchSemester.Batch)).limit(5).all()
        data_latest_batch_semester = list(reversed(data_latest_batch_semester_desc))

        list_lister_data, max_count, min_count = get_list_lister_data(data_latest_batch_semester)
        interval = 0
        # Make a 5 interval in max count and min count Ex. 100/5 = 20 then interval is 20
        if max_count and min_count:
            max_count = max_count + 1
            min_count = min_count - 1
            interval = int((max_count - min_count) / 5)
    
        if list_lister_data:
            return jsonify({'success': True, 'lister': list_lister_data, "max": max_count, "min": min_count, "interval": interval})
        else:
            return None

    except Exception as e:
        print("ERROR: ", e)
        return None
    
    
def processUpdatingSingleStudentRequirements(studentId, data):
    try:
        # Get Student Id
        student = db.session.query(Student, StudentRequirements).join(StudentRequirements, StudentRequirements.StudentId == Student.StudentId).filter(Student.StudentId == studentId).first()
       
        f137 = data.get('f137', False)
        # Update others using data.get
        f138 = data.get('f138', False)
        grade12 = data.get('grade12', False)
        grade11 = data.get('grade11', False)
        goodMoralSeal = data.get('good-moral-seal', False)
        sarForm = data.get('sar-form', False)
        psa = data.get('psa', False)
        diploma = data.get('diploma', False)
        grade10WitoutSeal = data.get('grade-10-without-seal', False)
        
        if student:
            student.StudentRequirements.F_137 = f137
            student.StudentRequirements.F_138 = f138
            student.StudentRequirements.Grade12 = grade12
            student.StudentRequirements.Grade11 = grade11
            student.StudentRequirements.GoodMoralSeal = goodMoralSeal
            student.StudentRequirements.SARForm = sarForm
            student.StudentRequirements.PSA = psa
            student.StudentRequirements.Diploma = diploma
            student.StudentRequirements.Grade10WithoutSeal = grade10WitoutSeal
            # Check if all data is true 
            if f137 and f138 and grade12 and grade11 and goodMoralSeal and sarForm and psa and diploma and grade10WitoutSeal:
                student.StudentRequirements.IsCompleted = True
            else: 
                student.StudentRequirements.IsCompleted = False
            db.session.commit()
            return jsonify({'success': True, "message": "Data updated successfully"}), 200
        else:
            db.session.rollback()
            return jsonify({'error': 'Student not found'}), 404
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
    


def noticeStudentsEmail():
    try:
        # Get Student Id
        student = db.session.query(Student, StudentRequirements).join(StudentRequirements, StudentRequirements.StudentId == Student.StudentId).filter(StudentRequirements.IsCompleted == False, StudentRequirements.NoticeCount < 3).all()

        if student:
            # Loop student list
            for data in student:
                documents = {
                    # Get student document
                    'Form 137' :data.StudentRequirements.F_137,
                    'Form 138' :data.StudentRequirements.F_138,
                    'Grade 12(Grades)' :data.StudentRequirements.Grade12,
                    'Grade 11(Grades)' :data.StudentRequirements.Grade11,
                    'Good Moral (Sealed)' :data.StudentRequirements.GoodMoralSeal,
                    'Sar Form' :data.StudentRequirements.SARForm,
                    'PSA' :data.StudentRequirements.PSA,
                    'Diploma (Grade 12)' :data.StudentRequirements.Diploma,
                    'Grade 10 (Without Seal)':data.StudentRequirements.Grade10WithoutSeal,
                }
                
                # Assuming not_recieve_documents is already defined as per your context
                not_recieve_documents = [key for key, value in documents.items() if value == False]

                # Joining each item in the list with a comma
                not_recieve_documents_str = ', '.join(not_recieve_documents)
                
                subject = ""
                if data.StudentRequirements.NoticeCount == 0:
                    subject = 'PUP Student Requirements (1st Notice)'
                elif data.StudentRequirements.NoticeCount == 1:
                    subject = 'PUP Student Requirements (2nd Notice)'
                else:
                    subject = 'PUP Student Requirements (Last Notice)'
                
                msg = Message(subject, sender='your_email@example.com',
                        recipients=[str(data.Student.Email)])
                # The message body should be the credentials details
                initial = "Mr." if data.Student.Gender == 1 else "Ms." 
                student_name = initial + " " + data.Student.FirstName 
                school_name = "PUP Quezon City Campus"
                office_name = "Registrar Office"
                contact_info = "admissions@example.com"

                email_body = f"Dear {student_name},\n\nI hope this email finds you well.\n\nI'm writing to remind you about the submission of the following documents required for your enrollment at {school_name}:\n\n{not_recieve_documents_str}\n\nYour prompt attention to this matter would be greatly appreciated. Should you have any questions or need assistance, feel free to reach out to {office_name} at {contact_info}.\n\nThank you for your cooperation.\n\nBest regards,\n{school_name}"

                data.StudentRequirements.NoticeCount += 1
                db.session.commit()
                msg.body = email_body   
                
                mail.send(msg)
            return {"success": True, "message": "Student notice successfully"}
        else:
            return {"success": True, "message": "No student incompleted"}
       
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
    


def getOutcomeRates(semester):
    try:
        rate_list = ["Passed", "Failed", "Dropout", "Incomplete", "Withdrawn"]
        if semester in [1, 2, 3]:
            # Get latest batch semester finalized
            data_latest_batch_semester = db.session.query(LatestBatchSemester) \
                .filter_by(Semester=semester, IsGradeFinalized=True) \
                .order_by(LatestBatchSemester.Batch.desc()) \
                .first()
            
            if data_latest_batch_semester:
                list_data = []
                list_year = []
                for batch_year in range(data_latest_batch_semester.Batch - 5, data_latest_batch_semester.Batch):
                    list_year.append(batch_year)
                    # Get the rates of the passing students
                    class_count = db.session.query(
                        func.sum(ClassSubjectGrade.Passed).label('total_passed'),
                        func.sum(ClassSubjectGrade.Failed).label('total_failed'),
                        func.sum(ClassSubjectGrade.Dropout).label('total_dropout'),
                        func.sum(ClassSubjectGrade.Incomplete).label('total_incomplete'),
                        func.sum(ClassSubjectGrade.Withdrawn).label('total_withdrawn')
                    ).join(ClassSubject, ClassSubject.ClassSubjectId == ClassSubjectGrade.ClassSubjectId)\
                    .join(Class, Class.ClassId == ClassSubject.ClassId)\
                    .join(Metadata, Metadata.MetadataId == Class.MetadataId)\
                    .filter(Metadata.Batch == batch_year, Metadata.Semester == semester)\
                    .first()
                    
                    enrolled_students = db.session.query(
                        func.sum(Metadata.TotalEnrolledStudents).label('total_enrolled')
                    ).filter(
                        Metadata.Batch == batch_year,
                        Metadata.Semester == semester
                    ).scalar()

                    total_enrolled_students = enrolled_students or 0
                    
                    total_passed = class_count.total_passed or 0
                    total_failed = class_count.total_failed or 0
                    total_dropout = class_count.total_dropout or 0
                    total_incomplete = class_count.total_incomplete or 0
                    total_withdrawn = class_count.total_withdrawn or 0
                    total = total_passed + total_failed + total_incomplete + total_dropout + total_withdrawn | 1
                    
                    failed_rate = math.ceil((total_failed / total) * 100)
                    dropout_rate = math.ceil((total_dropout / total) * 100)
                    incomplete_rate = math.ceil((total_incomplete / total) * 100)
                    withdrawn_rate = math.ceil((total_withdrawn / total) * 100)
                    passed_rate = 100 - failed_rate - dropout_rate - incomplete_rate - withdrawn_rate if total_passed > 0 else 0
                    
                    rate_data = {
                        "x": batch_year,
                        "Passed": passed_rate,
                        "Failed": failed_rate,
                        "Dropout": dropout_rate,
                        "Incomplete": incomplete_rate,
                        "Withdrawn": withdrawn_rate
                    }
                    
                    list_data.append(rate_data)
                
                # format_data = []
                # for type in ["PassedRates", "FailedRates", "DropoutRates", "IncompleteRates", "WithdrawnRates"]:
                #     data_dict = {
                #         "type": type,
                #         "results": []
                #     }
                #     for data in list_data:
                #         data_dict['results'].append({"x": (data['Year']), "y": data[type]})
                #     format_data.append(data_dict)
                        
                
                return jsonify({'success': True, 'data': list_data, 'rate_list': rate_list})
            else:
                return jsonify({'success': False})
        else:
            # Get latest batch semester finalized
            data_latest_batch_semester = db.session.query(LatestBatchSemester) \
                .filter_by(IsGradeFinalized=True) \
                .order_by(LatestBatchSemester.Batch.desc()) \
                .first()
            if data_latest_batch_semester:
                list_data = []
                for batch_year in range(data_latest_batch_semester.Batch - 5, data_latest_batch_semester.Batch):
                    
                    # Get the rates of the passing students
                    class_count = db.session.query(
                        func.sum(ClassSubjectGrade.Passed).label('total_passed'),
                        func.sum(ClassSubjectGrade.Failed).label('total_failed'),
                        func.sum(ClassSubjectGrade.Dropout).label('total_dropout'),
                        func.sum(ClassSubjectGrade.Incomplete).label('total_incomplete'),
                        func.sum(ClassSubjectGrade.Withdrawn).label('total_withdrawn')
                    ).join(ClassSubject, ClassSubject.ClassSubjectId == ClassSubjectGrade.ClassSubjectId)\
                    .join(Class, Class.ClassId == ClassSubject.ClassId)\
                    .join(Metadata, Metadata.MetadataId == Class.MetadataId)\
                    .filter(Metadata.Batch == batch_year)\
                    .first()
                    
                    enrolled_students = db.session.query(
                        func.sum(Metadata.TotalEnrolledStudents).label('total_enrolled')
                    ).filter(
                        Metadata.Batch == batch_year,
                    ).scalar()

                    total_enrolled_students = enrolled_students or 0
                    total_passed = class_count.total_passed or 0
                    total_failed = class_count.total_failed or 0
                    total_dropout = class_count.total_dropout or 0
                    total_incomplete = class_count.total_incomplete or 0
                    total_withdrawn = class_count.total_withdrawn or 0
                    total = total_passed + total_failed + total_incomplete + total_dropout + total_withdrawn | 1
                    
                    failed_rate = math.ceil((total_failed / total) * 100)
                    dropout_rate = math.ceil((total_dropout / total) * 100)
                    incomplete_rate = math.ceil((total_incomplete / total) * 100)
                    withdrawn_rate = math.ceil((total_withdrawn / total) * 100)
                    passed_rate = 100 - failed_rate - dropout_rate - incomplete_rate - withdrawn_rate if total_passed > 0 else 0
                    
                    rate_data = {
                        "x": batch_year,
                        "Passed": passed_rate,
                        "Failed": failed_rate,
                        "Dropout": dropout_rate,
                        "Incomplete": incomplete_rate,
                        "Withdrawn": withdrawn_rate
                    }
                    
                    list_data.append(rate_data)
                return jsonify({'success': True, 'data': list_data, 'rate_list': rate_list})
            return jsonify({'success': True})
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return e
    
def getBatchLatest():
    try:
        # Get latest batch semester
        latest_batch_semester = db.session.query(LatestBatchSemester)\
            .filter_by(IsGradeFinalized=True)\
            .order_by(LatestBatchSemester.Batch.desc())\
            .first()

        if latest_batch_semester:
            latest_batch = latest_batch_semester.Batch
        else:
            latest_batch = None  # Or handle the case where no batch is found
        return jsonify({"data": latest_batch, "success": True })
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': str(e)}), 500



def getGradDropWithdrawnRate(desired_year):
    try:
        
        if not desired_year:
            # Get current year
            desired_year = datetime.now().year
         
        # Get latest batch semester
        # Search year predicted
        search_batch = db.session.query(LatestBatchSemester).filter(LatestBatchSemester.Batch == desired_year, LatestBatchSemester.IsGradeFinalized == True, LatestBatchSemester.Semester >= 2).first()
        latest_batch = db.session.query(LatestBatchSemester).filter(LatestBatchSemester.IsGradeFinalized == True, LatestBatchSemester.Semester >= 2).order_by(LatestBatchSemester.Batch.desc()).first()
        last_batch = db.session.query(LatestBatchSemester).order_by(LatestBatchSemester.Batch).first()
        
        first_applicable_years = latest_batch.Batch - 5
        last_applicable_years = latest_batch.Batch + 3
        
        if search_batch:
            if search_batch.Batch <= latest_batch.Batch and search_batch.Batch >= first_applicable_years:
                class_count = db.session.query(
                        func.sum(ClassSubjectGrade.Passed).label('total_passed'),
                        func.sum(ClassSubjectGrade.Failed).label('total_failed'),
                        func.sum(ClassSubjectGrade.Dropout).label('total_dropout'),
                        func.sum(ClassSubjectGrade.Incomplete).label('total_incomplete'),
                        func.sum(ClassSubjectGrade.Withdrawn).label('total_withdrawn')
                    ).join(ClassSubject, ClassSubject.ClassSubjectId == ClassSubjectGrade.ClassSubjectId)\
                    .join(Class, Class.ClassId == ClassSubject.ClassId)\
                    .join(Metadata, Metadata.MetadataId == Class.MetadataId)\
                    .filter(Metadata.Batch == search_batch.Batch)\
                    .first()
                
                # Get all course
                course = db.session.query(Course).all()
                total_enrolled = 0
                for data in course:
                    enrolled_students = db.session.query(
                        func.sum(Metadata.TotalEnrolledStudents).label('total_enrolled')
                    ).filter(
                        Metadata.Batch == search_batch.Batch,
                        Metadata.Year == data.DurationYears,
                        Metadata.Semester == 1,
                        Metadata.CourseId == data.CourseId
                    ).scalar() or 0
                    total_enrolled += enrolled_students
                if not total_enrolled:
                    total_enrolled = 1
                total_graduated_students = db.session.query(func.count(CourseEnrolled.Status)) \
                        .filter_by(Status=1, BatchYearGraduated=search_batch.Batch) \
                        .scalar()
                
                total_passed = class_count.total_passed or 0
                total_failed = class_count.total_failed or 0
                total_dropout = class_count.total_dropout or 0
                total_incomplete = class_count.total_incomplete or 0
                total_withdrawn = class_count.total_withdrawn or 0
                
                
                total = total_passed + total_failed + total_incomplete + total_dropout + total_withdrawn | 1
               
                total_dropout_rate = math.ceil((total_dropout/total)*100)
                total_withdrawn_rate = math.ceil((total_withdrawn/total)*100)
                total_graduated_rate = math.ceil((total_graduated_students/total_enrolled)*100)
                
                
                data_dict = {
                    "graduated": {
                        "rate": total_graduated_rate,
                        "count": total_graduated_students
                    },
                    "dropout": {
                        "rate": total_dropout_rate,
                        "count": total_dropout
                    },
                    "withdrawn": {
                        "rate": total_withdrawn_rate,
                        "count": total_withdrawn
                    }
                }
                
                return jsonify({"data": data_dict, "predicted": False, "success": True})
        elif desired_year >= latest_batch.Batch:
            historical_years = []  # Example years
            
            historical_graduated = []  # Example summa cum laude counts
            historical_dropout = []  # Example cum laude counts
            historical_withdrawn = [] 
            
            historical_graduated_count=[]
            historical_dropout_count = []
            historical_withdrawn_count = []
            
            historical_enrolled_count = []  
            # Loop the latest.Batch as first and -5 it to loop for it
            for year_data in range(latest_batch.Batch - 5, desired_year + 1):
                if year_data <= latest_batch.Batch:
                    class_count = db.session.query(
                        func.sum(ClassSubjectGrade.Passed).label('total_passed'),
                        func.sum(ClassSubjectGrade.Failed).label('total_failed'),
                        func.sum(ClassSubjectGrade.Dropout).label('total_dropout'),
                        func.sum(ClassSubjectGrade.Incomplete).label('total_incomplete'),
                        func.sum(ClassSubjectGrade.Withdrawn).label('total_withdrawn')
                    ).join(ClassSubject, ClassSubject.ClassSubjectId == ClassSubjectGrade.ClassSubjectId)\
                    .join(Class, Class.ClassId == ClassSubject.ClassId)\
                    .join(Metadata, Metadata.MetadataId == Class.MetadataId)\
                    .filter(Metadata.Batch == year_data)\
                    .first() 
                    
                    # Get all course
                    course = db.session.query(Course).all()
                    total_enrolled = 0
                    for data in course:
                        enrolled_students = db.session.query(
                            func.sum(Metadata.TotalEnrolledStudents).label('total_enrolled')
                        ).filter(
                            Metadata.Batch == year_data,
                            Metadata.Year == data.DurationYears,
                            Metadata.Semester == 1,
                            Metadata.CourseId == data.CourseId
                        ).scalar() or 0
                        total_enrolled += enrolled_students
                    if not total_enrolled:
                        total_enrolled = 1
                    total_graduated = db.session.query(func.count(CourseEnrolled.Status)) \
                            .filter_by(Status=1, BatchYearGraduated=year_data) \
                            .scalar()
                        
                    total_passed = class_count.total_passed or 0
                    total_failed = class_count.total_failed or 0
                    total_dropout = class_count.total_dropout or 0
                    total_incomplete = class_count.total_incomplete or 0
                    total_withdrawn = class_count.total_withdrawn or 0
                    
                    
                    total = total_passed + total_failed + total_incomplete + total_dropout + total_withdrawn | 1
                    total_dropout_rate = math.ceil((total_dropout/total)*100)
                    total_withdrawn_rate = math.ceil((total_withdrawn/total)*100)
                    total_graduated_rate = math.ceil((total_graduated/total_enrolled)*100)
                    
                    data_dict = {
                        "graduated": {
                            "rate": total_graduated_rate,
                            "count": total_graduated
                        },
                        "dropout": {
                            "rate": total_dropout_rate,
                            "count": total_dropout
                        },
                        "withdrawn": {
                            "rate": total_withdrawn_rate,
                            "count": total_withdrawn
                        }
                    }
                
                    
                    historical_years.append(year_data)
                    
                    historical_graduated.append(total_graduated_rate)
                    historical_dropout.append(total_dropout_rate)
                    historical_withdrawn.append(total_withdrawn_rate)
                    
                    historical_enrolled_count.append(total_enrolled)
                    historical_graduated_count.append(total_graduated)
                    historical_dropout_count.append(total_dropout)
                    historical_withdrawn_count.append(total_withdrawn)
                else:
                    # Prepare data for linear regression
                    X = np.array(historical_years).reshape(-1, 1)
                    y_graduated = np.array(historical_graduated)
                    y_dropout = np.array(historical_dropout)
                    y_withdrawn = np.array(historical_withdrawn)
                    # y_total = np.array(historical_total_graduated)
                    
                    y_enrolled_count = np.array(historical_enrolled_count)
                    y_graduated_count = np.array(historical_graduated_count)
                    y_dropout_count = np.array(historical_dropout_count)
                    y_withdrawn_count = np.array(historical_withdrawn_count)

                    # Train linear regression models
                    model_graduated = LinearRegression().fit(X, y_graduated)
                    model_dropout = LinearRegression().fit(X, y_dropout)
                    model_withdrawn = LinearRegression().fit(X, y_withdrawn)
              
                    model_enrolled_count = LinearRegression().fit(X, y_enrolled_count)
                    model_graduated_count = LinearRegression().fit(X, y_graduated_count)
                    model_dropout_count = LinearRegression().fit(X, y_dropout_count)
                    model_withdrawn_count = LinearRegression().fit(X, y_withdrawn_count)

                    # Predict for the desired year
                    predicted_graduated = model_graduated.predict(np.array([[year_data]]))[0]
                    predicted_dropout = model_dropout.predict(np.array([[year_data]]))[0]
                    predicted_withdrawn = model_withdrawn.predict(np.array([[year_data]]))[0]
                    
                    predicted_enrolled_count = model_enrolled_count.predict(np.array([[year_data]]))[0]
                    predicted_graduated_count = model_graduated_count.predict(np.array([[year_data]]))[0]
                    predicted_dropout_count = model_dropout_count.predict(np.array([[year_data]]))[0]
                    predicted_withdrawn_count = model_withdrawn_count.predict(np.array([[year_data]]))[0]

                    historical_years.append(year_data)
                    historical_graduated.append(predicted_graduated)
                    historical_dropout.append(predicted_dropout)
                    historical_withdrawn.append(predicted_withdrawn)
                    historical_enrolled_count.append(round(predicted_enrolled_count))
                    historical_graduated_count.append(round(predicted_graduated_count))
                    historical_dropout_count.append(round(predicted_dropout_count))
                    historical_withdrawn_count.append(round(predicted_withdrawn_count))
            
            
            if desired_year in historical_years:
                index = historical_years.index(desired_year)
                graduated_rate = round((historical_graduated_count[index] / historical_enrolled_count[index])*100, 2)
                data_dict = {
                    "graduated": {
                        "rate": graduated_rate,
                        "count": historical_graduated_count[index]
                    },
                    "dropout": {
                        "rate": round(historical_dropout[index], 2),
                        "count": historical_dropout_count[index]
                    },
                    "withdrawn": {
                        "rate": round(historical_withdrawn[index], 2),
                        "count": historical_withdrawn_count[index]
                    }
                }
                
                return jsonify({"data": data_dict, "predicted": True, "success": True})
        return jsonify({"data": {}, "success": False})
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': str(e)}), 500




def get_total_distinct_students_by_status(status, year, programId):
    if programId == 0:
        return db.session.query(
            func.count(func.distinct(StudentClassSubjectGrade.StudentId))
        ).join(
            ClassSubject, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId
        ).join(
            Class, Class.ClassId == ClassSubject.ClassId
        ).join(
            Metadata, Metadata.MetadataId == Class.MetadataId
        ).filter(
            StudentClassSubjectGrade.AcademicStatus == status,
            Metadata.Batch == year
        ).scalar()
    else: 
        return db.session.query(
            func.count(func.distinct(StudentClassSubjectGrade.StudentId))
        ).join(
            ClassSubject, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId
        ).join(
            Class, Class.ClassId == ClassSubject.ClassId
        ).join(
            Metadata, Metadata.MetadataId == Class.MetadataId
        ).filter(
            StudentClassSubjectGrade.AcademicStatus == status,
            Metadata.Batch == year,
            Metadata.CourseId == programId
        ).scalar()
    
def get_total_sum_by_metric(metric, year):
    return db.session.query(
        func.sum(metric)
    ).join(
        ClassSubject, ClassSubject.ClassSubjectId == ClassSubjectGrade.ClassSubjectId
    ).join(
        Class, Class.ClassId == ClassSubject.ClassId
    ).join(
        Metadata, Metadata.MetadataId == Class.MetadataId
    ).filter(
        Metadata.Batch == year
    ).scalar() or 0

 # Predict the next 3 years
def predict_next_years_pfwd(data_list, years_to_predict=3):
    years = np.array(data_list['Year']).reshape(-1, 1)
    
    predictions = {'Year': [], 'Dropped': [], 'Failed': [], 'Withdrawn': []}
    future_years = [max(data_list['Year']) + i for i in range(1, years_to_predict + 1)]

    for key in ['Dropped', 'Failed', 'Withdrawn']:
        values = np.array(data_list[key])
        model = LinearRegression()
        model.fit(years, values)
        future_values = model.predict(np.array(future_years).reshape(-1, 1))
        predictions[key] = future_values.tolist()
    
    predictions['Year'] = future_years
    return predictions


def getPassFailedAndDropout(programId, startingYear, endingYear):
    try:
        # Get latest batch semester
        latest_batch_semester = db.session.query(LatestBatchSemester).filter_by(IsGradeFinalized = True).order_by(desc(LatestBatchSemester.Batch)).first()
        earliest_batch_semester = db.session.query(LatestBatchSemester).filter_by(IsGradeFinalized = True).order_by((LatestBatchSemester.Batch)).first()
       
        latest_batch = latest_batch_semester.Batch
        earliest_batch = earliest_batch_semester.Batch

        predict_length = endingYear - latest_batch

        # Initialize a dictionary to store total passing for each batch
        total_stats_by_year = []

        data_list = {
            "Year": [],
            "Withdrawn": [],
            "Dropped": [],
            "Failed": [],
        }

        for year in range(latest_batch, earliest_batch, -1):
            total_enrolled_students = db.session.query(func.sum(Metadata.TotalEnrolledStudents)) \
                .filter(Metadata.Batch == year) \
                .scalar()
                
            # total_graduated = db.session.query(func.sum(Metadata.TotalGraduatedStudents)).filter(Metadata.Batch == year).scalar() or 0

            metadata = db.session.query(Metadata).filter(Metadata.Batch == year).first()
            # total_passing = get_total_sum_by_metric(ClassSubjectGrade.Passed, year)
            # total_incomplete = get_total_sum_by_metric(ClassSubjectGrade.Incomplete, year)
            # total_failed = get_total_sum_by_metric(ClassSubjectGrade.Failed, year)
            # total_dropped = get_total_sum_by_metric(ClassSubjectGrade.Dropout, year)
            
            # total = (total_passing + total_incomplete + total_failed + total_dropped) or 1
            # dropout_rate_percentage = ((total_dropped / total) * 100) or 0
            # failed_rate_percentage = ((total_failed / total) * 100) or 0
            # total_enrolled_students = total_enrolled_students or 0

            # dropout_ceiling = math.ceil(dropout_rate_percentage)
            # failed_ceiling = math.ceil(failed_rate_percentage)
            # passed_value = 100 - dropout_ceiling - failed_ceiling
            
            total_distinct_student_failed = get_total_distinct_students_by_status(2, year, programId)
            total_distinct_student_incomplete = get_total_distinct_students_by_status(3, year, programId)
            total_distinct_student_withdrawn = get_total_distinct_students_by_status(4, year, programId)
            total_distinct_student_drop = get_total_distinct_students_by_status(5, year, programId)
            
            # print('\ntotal_distinct_student_drop:', year, total_distinct_student_drop)
            # print('total_distinct_student_withdrawn:', year, total_distinct_student_withdrawn)
            # print('total_distinct_student_failed:', year, total_distinct_student_failed)
            # print('total_distinct_student_incomplete:', year, total_distinct_student_incomplete)
            

            data_list['Year'].append(year)
            data_list['Withdrawn'].append(total_distinct_student_withdrawn)
            data_list['Dropped'].append(total_distinct_student_drop)
            data_list["Failed"].append(total_distinct_student_failed)
            print("NO ERROR IN WITHDRAWN")
            total_stats_by_year.append({
                "x": year,
                "Withdrawn": total_distinct_student_withdrawn,
                "Dropped": total_distinct_student_drop,
                "Failed": total_distinct_student_failed,
            })
       
        future_predictions = predict_next_years_pfwd(data_list, predict_length)
        
        predicted_year = []
        for i, year in enumerate(future_predictions['Year']):
            if year >= startingYear and year <= endingYear:
                print("YEAR: ", year)
                dropout_ceiling = max(math.ceil(future_predictions['Dropped'][i]), 0)
                failed_ceiling = max(math.ceil(future_predictions['Failed'][i]), 0)
                withdrawn_ceiling = max(math.ceil(future_predictions['Withdrawn'][i]), 0)
                
                # Create a model similar to total_stats
                predicted_year.append({
                    "x": year,
                    "Withdrawn": withdrawn_ceiling,
                    "Dropout": dropout_ceiling,
                    "Failed": failed_ceiling,
                })
        predicted_year.sort(key=lambda x: x['x'])

        # print(predicted_year)
        return jsonify({"data": predicted_year, "max_year": endingYear, "min_year": startingYear, "success": True})
    except Exception as e:
        print("ERROR: ", e )
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': str(e)}), 500
    
    
    
def getAllCourses():
    try:
        # Get latest batch semester
        all_program = db.session.query(Course).all()
        list_program = [{"ProgramId": 0, "Program":"All"}]
        if all_program:
            for course in all_program:
                list_program.append({"ProgramId": course.CourseId, "Program": course.CourseCode})  
            return jsonify({"data": list_program, "success": True })
        return jsonify({"message": "Data couldn't found", "success": False })
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': str(e)}), 500
