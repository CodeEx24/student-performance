from models import StudentClassGrade, ClassGrade, Class, Course, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, db, UniversityAdmin, ClassSubjectGrade, Metadata, Curriculum
from sqlalchemy import desc, distinct, func, and_
import re
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict

from datetime import date, datetime


from flask import session, jsonify
from static.js.utils import convertGradeToPercentage, checkStatus
from flask_mail import Message
from mail import mail
import pandas as pd
import random
import string
from sqlalchemy.orm import Session
from sqlalchemy import func


from collections import defaultdict

def getCurrentUser():
    current_user_id = session.get('user_id')
    return UniversityAdmin.query.get(current_user_id)


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

            # Find lowest, highest, and total enrollment counts
            for year, course_counts in course_year_counts.items():
                trend_item = {"x": year, **course_counts}
                trend_data.append(trend_item)

            return jsonify({'success': True, 'enrollment_trends': trend_data, 'course_list': list_course})
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
            CourseGrade, Course).join(Course, Course.CourseId == CourseGrade.CourseId).order_by(CourseGrade.Batch, CourseGrade.CourseId).all()
        
        list_course = []
        
        if data_course_grade:
            course_year_grades = defaultdict(dict)

            for course_grade in data_course_grade:
                # Check if course_grade.Course.CourseCode existing in list_course
                if course_grade.Course.CourseCode not in list_course:
                    list_course.append(course_grade.Course.CourseCode)
                
                year = course_grade.CourseGrade.Batch
                course_id = course_grade.Course.CourseCode
                
                grade = convertGradeToPercentage(course_grade.CourseGrade.Grade)

                if year not in course_year_grades:
                    course_year_grades[year] = {"x": year}

                course_year_grades[year][course_id] = grade

            # Convert the data into a list of dictionaries
            formatted_data = list(course_year_grades.values())
            return jsonify({'success': True, 'list_course': list_course, 'course_performance': formatted_data})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return e


def getAllClassData(skip, top, order_by, filter):
    try:
        class_grade_query = db.session.query(Class, Metadata,  Course, ClassGrade).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
        
        
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
                    
                    if column_name.strip() == 'ClassName':
                        split_values = value.split(' ')
                        
                        if len(split_values) >= 2:
                            # Check split values if have a number
                            if any(char.isdigit() for char in split_values[-1]):
                                batch_section = split_values[-1]
                                course_code = ' '.join(split_values[:-1])
                                column_arr_1 = getattr(Course, 'CourseCode')
                                year, section = None, None
                                
                                if '-' in batch_section:
                                    year, section = batch_section.split('-')
                                    if section:
                                        column_arr_3 = getattr(Class, 'Section')
                                    column_arr_2 = getattr(Metadata, 'Year')
                                else:
                                    year = batch_section
                                    column_arr_2 = getattr(Metadata, 'Year')
                            else:
                                course_code = ' '.join(split_values)
                                year, section = None, None
                                column_arr_1 = getattr(Course, 'CourseCode')

                            # Append column_arr_1
                            filter_conditions.append(
                                func.lower(column_arr_1).like(f'%{split_values[0]}%')
                            )
                            # Check if year then append
                            if year:
                                filter_conditions.append(Metadata.Year == int(year))
                                
                            if section:
                                filter_conditions.append(
                                    Class.Section == int(section)
                                )
                            continue
                        elif len(split_values) == 1:
                            course_code, year, section = None, None, None
                            # check if value contains "-" and digit in it
                            if '-' in value and any(x.isdigit() for x in value):
                                year, section = value.split('-')
                                column_arr_2 = Metadata.Year
                                column_arr_3 = Class.Section
                            else:
                                course_code = value
                                column_arr_1 = getattr(Course, 'CourseCode')
                            
                            if course_code:
                                filter_conditions.append(column_arr_1.like(f'%{course_code.upper()}%'))

                            if year:
                                filter_conditions.append(
                                    column_arr_2 == int(year)
                                )
                            
                            if section:
                                filter_conditions.append(
                                    column_arr_3 == int(section)
                                )
                            continue
                    elif column_name.strip() == 'Course':
                        column_str = getattr(Course, 'Name')
                    elif column_name.strip() == 'Grade':
                        filter_conditions.append(
                            ClassGrade.Grade == value
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
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = class_grade_query.filter(and_(*filter_conditions))
        # print('FILTER: ', filter_query.statement.compile().params)
        
         # Apply sorting logic
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'Course':
                order_attr = getattr(Course, 'Name')
            elif order_by.split(' ')[0] == "Batch":
                order_attr = getattr(Metadata, "Batch")
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, 'Semester')
            elif order_by.split(' ')[0] == 'Grade':
                order_attr = getattr(ClassGrade, 'Grade')
            else:
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(Course.CourseCode), desc(Metadata.Year), desc(Class.Section))
                else:
                    order_query = filter_query.order_by(Course.CourseCode, Metadata.Year, Class.Section)

            # Check if order_by contains space
            if not order_by.split(' ')[0] == "ClassName":
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.CourseId), Metadata.Year, Class.Section)
        
        class_grade_main_query = order_query.offset(skip).limit(top).all()
        

        if class_grade_main_query:
            list_classes = []
            seen_class_ids = set()  # Initialize a set to track seen ClassIds

            for class_subject_grade in class_grade_main_query:
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
                        grade_value = 0.00
                        
                    class_obj = {
                        'ClassId': class_id,
                        'ClassName': f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Metadata.Year}-{class_subject_grade.Class.Section}",
                        'Semester': class_subject_grade.Metadata.Semester,
                        "Course": class_subject_grade.Course.Name,
                        "Batch": class_subject_grade.Metadata.Batch,
                        "Grade": grade_value
                    }

                    # Add class_id to the seen_class_ids set
                    seen_class_ids.add(class_id)

                    # Add class_obj to the list_classes
                    list_classes.append(class_obj)

            # Return the list of class objects
            return {'result': list_classes, 'count': 50}
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getClassPerformance(class_id):
    try:
        class_grade = (
            db.session.query(
                ClassGrade, Course, Class, Metadata
            )
            .join(Class, Class.ClassId == ClassGrade.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .filter(ClassGrade.ClassId == class_id)
            .first()
        )

        
        if class_grade:

            # Calculate class name
            class_name = f"{class_grade.Course.CourseCode} {class_grade.Metadata.Year}-{class_grade.Class.Section} ({class_grade.Metadata.Batch})"
            num_class_batch = class_grade.Metadata.Batch
            num_class_section = class_grade.Class.Section

            dict_class_grade = {
                'Class': class_name,
                'Batch': num_class_batch,
                'ListGrade': [],
                'PresidentLister': class_grade.ClassGrade.PresidentsLister,
                'DeanLister': class_grade.ClassGrade.DeansLister
            }
            
            list_grade = []
            for i in range(1, class_grade.Metadata.Year+1):
                batch = class_grade.Metadata.Batch - class_grade.Metadata.Year + i
                class_grade_result = (
                    db.session.query(
                        Class,
                        Metadata,
                        ClassGrade,
                    )
                    .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                    .filter(Metadata.Year == i, Metadata.Batch == batch, Class.Section == num_class_section)
                    .first()

                )

                list_grade.append(
                    {'x': class_grade_result.Metadata.Batch, 'y': convertGradeToPercentage(class_grade_result.ClassGrade.Grade)})
                
            dict_class_grade['ListGrade'].extend(list_grade)

            return (dict_class_grade)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def processAddingStudents(data, excelType=False):
    try:
        print("HERE")
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
                student_name = row['Name']
                student_email = row['Email']
                student_mobile =  str(row['Phone Number'])
                student_address = row['Address'] # OK
                student_gender = row['Gender'] # OK
                student_course = row['Course Code']
                student_date_enrolled = row['Date Enrolled']
                student_batch = row['Batch'] # OK

                if student_mobile:
                    # Check for length of phone number if 10 add 0 in first
                    if len(student_mobile) == 10:
                        student_mobile = '0' + student_mobile
                    
            
                # Check if Date Enrolled is a valid date format
                if student_date_enrolled is not None:
                    # Check if it is in date format then convert it into YYYY-MM-DD
                    if isinstance(student_date_enrolled, datetime):
                        student_date_enrolled = student_date_enrolled.strftime("%Y-%m-%d")
                        print('student_date_enrolled: ', student_date_enrolled)
                    else:
                        errors.append({
                            'StudentNumber': student_number,
                            'Name': student_name,
                            'Email': student_email,
                            'Phone': student_mobile,
                            'Address': student_address,
                            'Gender': student_gender,
                            'CourseCode': student_course,
                            'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                            'Batch': student_batch,
                            'Error': 'Invalid Date Enrolled format'
                        })
                        continue
                    
                    
                # Check if Batch is a valid format (e.g., numeric)
                if not str(student_batch).isdigit():
                    errors.append({
                        'StudentNumber': student_number,
                        'Name': student_name,
                        'Email': student_email,
                        'Phone': student_mobile,
                        'Address': student_address,
                        'Gender': student_gender,
                        'CourseCode': student_course,
                        'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                        'Batch': student_batch,
                        'Error': 'Invalid Batch format'
                    })
                    continue
                
                # Check if Email is a valid format
                if not is_valid_email(student_email):
                    errors.append({
                        'StudentNumber': student_number,
                        'Name': student_name,
                        'Email': student_email,
                        'Phone': student_mobile,
                        'Address': student_address,
                        'Gender': student_gender,
                        'CourseCode': student_course,
                        'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                        'Batch': student_batch,
                        'Error': 'Invalid Email format'
                    })
            
                    continue
                
                # Check if Phone Number is a valid format
                if student_mobile and not is_valid_phone_number(student_mobile):
                    errors.append({
                        'StudentNumber': student_number,
                        'Name': student_name,
                        'Email': student_email,
                        'Phone': student_mobile,
                        'Address': student_address,
                        'Gender': student_gender,
                        'CourseCode': student_course,
                        'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                        'Batch': student_batch,
                        'Error': 'Invalid Phone Number format'
                    })
                
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
                    
                    new_course_enrolled = CourseEnrolled(
                        CourseId=course.CourseId,
                        StudentId=new_student.StudentId,
                        DateEnrolled=student_date_enrolled,
                        Status=1,
                        CurriculumYear=student_batch
                    )
                    
                    # # Add the new course enrolled to the session
                    db.session.add(new_course_enrolled)
                    db.session.commit()
                    
                    msg = Message('Your current PUP Account has been granted.', sender='your_email@example.com',
                                recipients=[str(new_student.Email)])
                    # The message body should be the credentials details
                    msg.body = f"Your current PUP Account has been granted. \n\n Email: {str(new_student.Email)} \n Password: {str(password)} \n\n Please change your password after you log in. \n\n Thank you."
                    
                    # mail.send(msg)
                    
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
                    if student_number_data:
                        # Append the Student Number, Email and what type error it is
                        errors.append({
                            'StudentNumber': student_number,
                            'Name': student_name,
                            'Email': student_email,
                            'Phone': student_mobile,
                            'Address': student_address,
                            'Gender': student_gender,
                            'CourseCode': student_course,
                            'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                            'Batch': student_batch,
                            'Error': 'Student Number already exist'
                        })
                    else:
                        errors.append({
                            'StudentNumber': student_number,
                            'Name': student_name,
                            'Email': student_email,
                            'Phone': student_mobile,
                            'Address': student_address,
                            'Gender': student_gender,
                            'CourseCode': student_course,
                            'DateEnrolled': student_date_enrolled,  # Adding the original string for reference
                            'Batch': student_batch,
                            'Error': 'Email already exist'
                        })
                    
            if errors and list_student_data:
                db.session.rollback()
                return jsonify({'warning': 'Some data cannot be added.', 'errors': errors, 'data': list_student_data}), 500
            if errors and not list_student_data:
                db.session.rollback()
                return jsonify({'error': 'Adding data failed.', 'errors': errors}), 500
            else:        
                return  jsonify({'result': 'Data added successfully', 'data': list_student_data}), 200
        else:
            print('data: ', data)
            if data:
                student_number = data['StudentNumber'].strip()
                student_name = data['Name']
                student_email = data['Email'].strip()
                student_gender = data['Gender'] # OK
                student_mobile =  str(data['MobileNumber']).strip()
                student_course = data['CourseCode'].strip()
                student_date_enrolled = data['DateEnrolled']
                student_batch = data['Batch'] # OK
                
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
                        
                        print('student_date_enrolled: ', student_date_enrolled)
                    except Exception as e:
                        return jsonify({'error': 'Invalid Date Enrolled format'}), 400
              
                # Check if Batch is a valid format (e.g., numeric)
                if not type(student_batch) == int:
                    # Return error
                    # print
                    print("BATCH IS NOT NUMERIC")
                    return jsonify({'error': 'Invalid Batch format'}), 400
                
                print("AFTER BAATCH")
                # Check if Email is a valid format
                if not is_valid_email(student_email):
                    # Return error
                    # print
                    print("INVALID EMAIL")
                    return jsonify({'error': 'Invalid Email format'}), 400
                print("AFTER EMAIL")
                # Check if Phone Number is a valid format
                if student_mobile and not is_valid_phone_number(student_mobile):
                    # Return error
                    # print
                    print("INVALID PHONE NUMBER")
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

                    course = db.session.query(Course).filter_by(CourseCode=student_course).first()
                    
                    
                # Add the new student in the database

                    # Ensure the mobile number has a leading zero
                    if not student_mobile.startswith('0'):
                        student_mobile = '0' + student_mobile
                    
                    print("VALID USER: ", student_number, student_name, student_email, student_mobile, gender, password)
                    new_student = Student(
                        StudentNumber=student_number,
                        Name=student_name,
                        Email=student_email,
                        MobileNumber=str(student_mobile),
                        Gender=gender,
                        Password=generate_password_hash(password)
                    )
                    
                    print("AFTER")
                    print('new_student.StudentId: ', new_student)
                    db.session.add(new_student)
                    db.session.flush()
                    print('new_student: ', new_student)
                    new_course_enrolled = CourseEnrolled(
                        CourseId=course.CourseId,
                        StudentId=new_student.StudentId,
                        DateEnrolled=student_date_enrolled,
                        Status=1,
                        CurriculumYear=student_batch
                    )
                    print("AFTER 2")
                    # # Add the new course enrolled to the session
                    db.session.add(new_course_enrolled)
                    db.session.commit()
                    
                    msg = Message('Your current PUP Account has been granted.', sender='your_email@example.com',
                                recipients=[str(new_student.Email)])
                    # The message body should be the credentials details
                    msg.body = f"Your current PUP Account has been granted. \n\n Email: {str(new_student.Email)} \n Password: {str(password)} \n\n Please change your password after you log in. \n\n Thank you."
                    
                    mail.send(msg)
                    # Return data added success
                    # print
                    
                    print("DATA ADDED SUCCESSFULLY")
                    return jsonify({'result': 'Data added successfully'}), 200
                    
                else:
                    if student_number_data:
                        print("STUDENT NUMBER ALREADY EXIST")
                        return jsonify({'error': 'Student Number already exist'}), 400
                    else:
                        # Return email already exist
                        # print
                        print("EMAIL ALREADY EXIST")
                        return jsonify({'error': 'Email already exist'}), 400
                    

    except Exception as e:
        db.session.rollback()
        print("ERROR: ", e)
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
    
    
def processAddingClass(file):
    try:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        list_new_class_data = []
        
        errors = []

        
        for index, row in df.iterrows():
            course_code = row['Course Code']
            section = int(row['Section'])
            year = int(row['Year Level'])
            semester = int(row['Semester'])
            batch = int(row['Batch'])

            course = db.session.query(Course).filter_by(CourseCode=course_code).first()
            
            if not course:
                errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Course Not Exist"})
                continue
                    
            metadata = db.session.query(Metadata).filter_by(CourseId=course.CourseId, Year=year, Semester=semester, Batch=batch).first()

            if not metadata:
                errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Curriculum not exist"})
                continue

            if course and metadata:
                curriculum = db.session.query(Curriculum).filter_by(MetadataId=metadata.MetadataId).all()
                if curriculum:
                    class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(
                        Metadata.CourseId==course.CourseId, Metadata.Year==year, Class.Section==section, Metadata.Semester==semester, Metadata.Batch==batch).first()

                    if not class_data:
                        class_name = f"{course_code} {year}-{section}"
                        course_name = course.Name
                        new_class = Class(
                            Section=section,
                            IsGradeFinalized=False,
                            # Transition to metadata
                            MetadataId = metadata.MetadataId
                            # Semester=semester,
                            # Batch=batch,
                            # CourseId=course.CourseId,
                            # Year=year
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
                            "Semester": metadata.Semester,
                            "Batch": metadata.Batch
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
                            db.session.commit()
                    else:
                        errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Class already exist"})
                else:
                    errors.append({"CourseCode": course_code, "Section": section, "Year": year, "Semester": semester, "Batch": batch, "Error": "Curriculum not exist"})
            
                
        if errors and list_new_class_data:  
            db.session.rollback()
            return jsonify({'warning': "Some data cannot be added.", 'errors': errors, 'data': list_new_class_data}), 400
        if errors and not list_new_class_data:
            db.session.rollback()
            return jsonify({'error': 'Adding data failed.', 'errors': errors}), 400
        else:
            
            return jsonify({'result': 'Data added successfully', 'data': list_new_class_data}), 200
 
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500


    
 
def processClassStudents(file, class_id):
    try:
        print("HERE IN processClassStudents")
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        df = pd.read_excel(file)
        
        list_student_added = []
        errors = []
        
        # Find the class
        class_data = db.session.query(Class).filter_by(ClassId=class_id).first()
        if class_data:
            # Check for student first if exist in df
            for index, row in df.iterrows():
                student_number = str(row['Student Number'])
                student_date_enrolled = row['Date Enrolled']
                student_class_grade_exist = False;
                
                if not student_number:
                    errors.append({
                        'StudentNumber': 'N/A',
                        'DateEnrolled': student_date_enrolled,
                        'Error': 'Student Number must have a value'
                    })
                    continue
                
                if student_date_enrolled:
                    if isinstance(student_date_enrolled, datetime):
                        student_date_enrolled = student_date_enrolled.strftime("%Y-%m-%d")
                    else:
                        errors.append({
                            'StudentNumber': student_number,
                            'DateEnrolled': "N/A",
                            'Error': 'Invalid Date Enrolled format'
                        })
                        continue
                
                if not student_date_enrolled:
                    errors.append({
                        'StudentNumber': student_number,
                        'DateEnrolled': 'N/A',
                        'Error': 'Date Enrolled must have a value'
                    })
                    continue
           
                student_data = db.session.query(Student).filter_by(StudentNumber=student_number).first()

                if not student_data:
                    
                    errors.append({
                        'StudentNumber': student_number,
                        'DateEnrolled': student_date_enrolled,
                        'Error': 'Student Number does not exist'
                    })
                    continue
                
                else:
                    class_subject_data = db.session.query(ClassSubject).filter_by(ClassId=class_id).all()
                    if class_subject_data:
                        # for loop of it
                        for class_subject in class_subject_data:
                        
                            # Check if not class_grade_exist then create and set it to True
                            if not student_class_grade_exist:
                                student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId=student_data.StudentId, ClassId=class_id
                                ).all()
                                if not student_class_grade:
                                    new_student_class_grade = StudentClassGrade(
                                        StudentId=student_data.StudentId,
                                        ClassId=class_id
                                    )
                                    db.session.add(new_student_class_grade)
                                    db.session.flush()
                                    student_class_grade_exist = True;
                                
                                    
                            subject_data = db.session.query(Subject).filter_by(SubjectId=class_subject.SubjectId).first()
                            
                            # check if student_class_subject_grade_exist
                            student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId=student_data.StudentId, ClassSubjectId=class_subject.ClassSubjectId).first()
                            if not student_class_subject_grade:
                                new_student_class_subject_grade = StudentClassSubjectGrade(
                                    StudentId=student_data.StudentId,
                                    ClassSubjectId=class_subject.ClassSubjectId,
                                    DateEnrolled=student_date_enrolled
                                )
                                db.session.add(new_student_class_subject_grade)
                                db.session.commit()
                            
                                # Append list_student_added
                                list_student_added.append({
                                    "StudentNumber": student_number,
                                    "SubjectCode": subject_data.SubjectCode
                                })
                            # Add If else here if there  is something error want to pop-up
                    else:
                        # return no class subject yet
                        return jsonify({'error': 'No class subject yet'}), 400
  
            if errors and not list_student_added:
                db.session.rollback()
                return jsonify({'error': 'Adding students failed', 'errors': errors}), 400
            else:
                return jsonify({'result': 'Data added successfully'}), 200
        else:
            # return error with message cannot find the class
            return jsonify({'error': 'Cannot find the class'}), 400    
            
    except Exception as e:
        
        db.session.rollback()
        return jsonify({'errorException': 'An error occurred while processing the file'}), 500
            
            
            
    #         class_subject_data = db.session.query(ClassSubject).filter_by(ClassId=class_id).all()
    #         if class_subject_data:
    #             # for loop the class_subject_data
                
    #             for class_subject in class_subject_data:                    
    #                 # Create StudentClassSubjectGrade for all ClassSubjectId 
    #                 for index, row in df.iterrows():
    #                     class_grade_exist = False;
    #                     student_number = row['Student Number']
    #                     date_enrolled = row['Date Enrolled'].date()
                        
    #                     # Get the student data
    #                     student_data = db.session.query(Student).filter_by(StudentNumber=student_number).first()
    #                     if student_data:
    #                         # Check if student_class_subject_grade exist
    #                         student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId=student_data.StudentId, ClassSubjectId=class_subject.ClassSubjectId).first()
    #                         if student_class_subject_grade:
    #                             # Find the subject 
    #                             subject_data = db.session.query(Subject).filter_by(SubjectId=class_subject.SubjectId).first()
                        
    #                             list_student_class_subject_exist.append({
    #                                 "StudentNumber": student_number,
    #                                 "SubjectCode": subject_data.SubjectCode
    #                             }) 
    #                         else:
                                
    #                             if not class_grade_exist:
    #                                 # Check if studentClassGrade already exist if not create one
    #                                 student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId=student_data.StudentId, ClassId=class_id).first()
                                    
    #                                 if not student_class_grade:
    #                                     new_student_class_grade = StudentClassGrade(
    #                                         StudentId=student_data.StudentId,
    #                                         ClassId=class_id
    #                                     )
    #                                     db.session.add(new_student_class_grade)
    #                                     db.session.flush()
    #                                     class_grade_exist = True;
                                
    #                             subject_data = db.session.query(Subject).filter_by(SubjectId=class_subject.SubjectId).first()
                                
    #                             new_student_class_subject_grade = StudentClassSubjectGrade(
    #                                 StudentId=student_data.StudentId,
    #                                 ClassSubjectId=class_subject.ClassSubjectId,
    #                                 DateEnrolled=date_enrolled
    #                             )
    #                             db.session.add(new_student_class_subject_grade)
    #                             db.session.commit()
                                
    #                             # Append list_student_added
    #                             list_student_added.append({
    #                                 "StudentNumber": student_number,
    #                                 "SubjectCode": subject_data.SubjectCode
    #                             })
    #                     else:
    #                         if student_number not in list_student_number_not_exist:
    #                             list_student_number_not_exist.append(student_number)   
    #         else:
    #             # return no class subject yet
    #             return jsonify({'error': 'No class subject yet'}), 400
    #     else:
    #         # return error with message cannot find the class
    #         return jsonify({'error': 'Cannot find the class'}), 400
        
    #     if list_student_number_not_exist:
            
    #     if list_student_class_subject_exist:
            
    #     if not list_student_added:
        
    #     # Check if length of list_student_number_not_exist or list_student_class_subject_exist
    #     if (list_student_number_not_exist or list_student_class_subject_exist) and list_student_added:
    #         db.session.rollback()
    #         return jsonify({'error': 'Some data cannot be added', 'errors': {'student_number_not_exist': list_student_number_not_exist, 'student_class_subject_exist': list_student_class_subject_exist}}), 400
    #     elif (list_student_number_not_exist or list_student_class_subject_exist) and not list_student_added:
    #         db.session.rollback()
    #         return jsonify({'error': 'Adding students failed', 'errors': {'student_number_not_exist': list_student_number_not_exist, 'student_class_subject_exist': list_student_class_subject_exist}}), 400
    #     else:
    #         return jsonify({'result': 'Data added successfully'}), 200

    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({'error': 'An error occurred while processing the file'}), 500


def getStudentData(skip, top, order_by, filter):
    try:
        student_query = (
            db.session.query(Student, CourseEnrolled, Course).join(CourseEnrolled, CourseEnrolled.StudentId == Student.StudentId).join(Course, Course.CourseId == CourseEnrolled.CourseId)
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
                    elif column_name.strip() == 'Name':
                        column_str = getattr(Student, 'Name')
                    elif column_name.strip() == 'Email':
                        column_str =  getattr(Student, 'Email')     
                    elif column_name.strip() == 'MobileNumber':
                        column_str = getattr(Student, 'MobileNumber')
                    elif column_name.strip() == 'CourseCode':
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
            elif order_by.split(' ')[0] == "Name":
                order_attr = getattr(Student, 'Name')
            elif order_by.split(' ')[0] == 'Email':
                order_attr = getattr(Student, 'Email')
            elif order_by.split(' ')[0] == 'Gender':
                order_attr = getattr(Student, 'Gender')
            elif order_by.split(' ')[0] == 'MobileNumber':
                order_attr = getattr(Student, 'MobileNumber')
            elif order_by.split(' ')[0] == 'CourseCode':
                order_attr = getattr(Course, 'CourseCode')
            elif order_by.split(' ')[0] == 'DateEnrolled':
                order_attr = getattr(CourseEnrolled, 'DateEnrolled')
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(CourseEnrolled, 'CurriculumYear')
           
           
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
                dict_student = {
                    "StudentId": data.Student.StudentId,
                    "StudentNumber": data.Student.StudentNumber,
                    "Name": data.Student.Name,
                    "Email": data.Student.Email,
                    "MobileNumber": data.Student.MobileNumber,
                    "Gender": "Male" if data.Student.Gender == 1 else "Female",
                    "CourseCode": data.Course.CourseCode,
                    "DateEnrolled": data.CourseEnrolled.DateEnrolled.strftime('%Y-%m-%d'),
                    "Batch": data.CourseEnrolled.CurriculumYear
                }
                # Append the data
                list_student_data.append(dict_student)
            return jsonify({"result": list_student_data, "count":total_count})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getStudentAddOptions():
    try:
      # Make gender options
        genderOptionList = [{"Gender":"Male"},{"Gender":"Female"}]
        # Make course options
        courseOptionList = []
        course_data = db.session.query(Course).all()
        if course_data:
            for course in course_data:
                courseOptionList.append({"CourseCode": course.CourseCode})
        
        # Make batch options for prev year, current year and future year. For example 2024 is current year then it should be 2023, 2024, 2025
        
        
        current_year = datetime.now().year
        batchOptionList = [{"Batch": current_year+1}, {"Batch": current_year},{"Batch": current_year-1}]
        
        return jsonify({'result':{"genderOptions": genderOptionList, "courseOptions": courseOptionList, "batchOptions": batchOptionList}})
        
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e})

    
def getAllClassSubjectData():
    try:
        data_class_subject = (
            db.session.query(ClassSubject, Subject, Class, Metadata, Course, Faculty).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).join(Class, Class.ClassId == ClassSubject.ClassId).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(Faculty, Faculty.FacultyId == ClassSubject.FacultyId).order_by(desc(Metadata.Batch),desc(Metadata.Semester), (Subject.Name)).all()
        )
        

        
        if data_class_subject:
                # For loop the data_student and put it in dictionary
            list_class_subject = []
            for class_subject in data_class_subject:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_subject.Course.CourseCode} {class_subject.Metadata.Year}-{class_subject.Class.Section}"
                middle_name = class_subject.Faculty.middle_name if class_subject.Faculty.middle_name else ""
                full_name = f"{class_subject.Faculty.last_name}, {class_subject.Faculty.first_name} {middle_name}"
                
                dict_class_subject = {
                    "Section Code": class_name,
                    "Subject": class_subject.Subject.Name,
                    "Teacher":full_name,
                    "Schedule": class_subject.ClassSubject.Schedule,
                    'Batch': class_subject.Metadata.Batch,
                    'Semester': class_subject.Metadata.Semester
                }
                # # Append the data
                list_class_subject.append(dict_class_subject)
            return jsonify({'result': list_class_subject})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    

def getStudentClassSubjectGrade(skip, top, order_by, filter):
    try:
        # Initial query
        query = (
            db.session.query(
                ClassSubject,
                StudentClassSubjectGrade,
                Subject,
                Class,
                Metadata,
                Course,
                Student
            )
            .join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId)
            # .filter(ClassSubject.FacultyId == str_teacher_id, Class.Batch >= current_year-4)
        )

        # Parse and apply filters
        
        filter_conditions = []
        # Split filter string by 'and'
        # append the str_teacher_id
        # filter_conditions.append(
        #     ClassSubject.FacultyId == str_teacher_id
        # )

        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split("),'")[0]
                    value = part.split("'")[1]
                    column_str = None
                    
                    if column_name.strip() == 'Class':
                        split_values = value.split(' ')
                        
                        if len(split_values) >= 2:
                            # Check split values if have a number
                            if any(char.isdigit() for char in split_values[-1]):
                                batch_section = split_values[-1]
                                course_code = ' '.join(split_values[:-1])
                                column_arr_1 = getattr(Course, 'CourseCode')
                                year, section = None, None
                                
                                if '-' in batch_section:
                                    year, section = batch_section.split('-')
                                    if section:
                                        column_arr_3 = getattr(Class, 'Section')
                                    column_arr_2 = getattr(Metadata, 'Year')
                                else:
                                    year = batch_section
                                    column_arr_2 = getattr(Metadata, 'Year')
                            else:
                                course_code = ' '.join(split_values)
                                year, section = None, None
                                column_arr_1 = getattr(Course, 'CourseCode')

                            # Append column_arr_1
                            filter_conditions.append(
                                func.lower(column_arr_1).like(f'%{split_values[0]}%')
                            )
                            # Check if year then append
                            if year:
                                filter_conditions.append(Metadata.Year == int(year))
                                
                            if section:
                                filter_conditions.append(
                                    Class.Section == int(section)
                                )
                            continue
                        elif len(split_values) == 1:
                            course_code, year, section = None, None, None
                            # check if value contains "-" and digit in it
                            if '-' in value and any(x.isdigit() for x in value):
                                year, section = value.split('-')
                                column_arr_2 = Metadata.Year
                                column_arr_3 = Class.Section
                            else:
                                course_code = value
                                column_arr_1 = getattr(Course, 'CourseCode')
                            
                            if course_code:
                                filter_conditions.append(column_arr_1.like(f'%{course_code.upper()}%'))

                            if year:
                                filter_conditions.append(
                                    column_arr_2 == int(year)
                                )
                            
                            if section:
                                filter_conditions.append(
                                    column_arr_3 == int(section)
                                )
                            continue
                    elif column_name.strip() == 'StudentName':
                        column_str = getattr(Student, 'Name')
                    elif column_name.strip() == 'StudentNumber':
                        column_str =  getattr(Student, 'StudentNumber')     
                    elif column_name.strip() == 'SubjectCode':
                        column_str = getattr(Subject, 'SubjectCode')
                 
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

                    if column_name.strip() == 'Grade':
                        column_num = StudentClassSubjectGrade.Grade
                    elif column_name.strip() == 'Batch':
                        column_num = Metadata.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = Metadata.Semester
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = query.filter(and_(*filter_conditions))

 
        # Apply sorting logic
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Student, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == "StudentName":
                order_attr = getattr(Student, 'Name')
            elif order_by.split(' ')[0] == 'Grade':
                order_attr = getattr(StudentClassSubjectGrade, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'SubjectCode':
                order_attr = getattr(Subject, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            else:
                print("CLASS ORDER BY: ", order_by)

                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(Course.CourseCode), desc(Metadata.Year), desc(Class.Section))
                
                else:
                    order_query = filter_query.order_by(Course.CourseCode, Metadata.Year, Class.Section)
                # close the if_order by and go to next line of it

            # Check if order_by contains space
            if not order_by.split(' ')[0] == "Class":
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                    print("ORDER: ", order_query.statement.compile().params)
                else:
                    order_query = filter_query.order_by(order_attr)
                    print("ORDER: ", order_query.statement.compile().params)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(
                desc(Course.CourseCode), desc(Metadata.Batch), desc(Metadata.Year), desc(Metadata.Semester), Student.Name
            )

        # Check if order_query and filter query exists:

        # Apply skip and top
        result_all = order_query.all()
        # print('result_all: ', result_all)
        result = result_all[skip: skip + top]
        total_count = order_query.count()
        

        if result:
            list_data_class_subject_grade = []
            unique_classes = set()
     
            for class_subject_grade in result:
               
                class_name = f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Metadata.Year}-{class_subject_grade.Class.Section}"

                dict_class_subject_grade = {
                    'ClassSubjectId': class_subject_grade.ClassSubject.ClassSubjectId ,
                    'StudentId': class_subject_grade.Student.StudentId,
                    'StudentNumber': class_subject_grade.Student.StudentNumber,
                    'StudentName': class_subject_grade.Student.Name,
                    'Class': class_name,
                    'Batch': class_subject_grade.Metadata.Batch,
                    'Semester': class_subject_grade.Metadata.Semester,
                    'Grade': class_subject_grade.StudentClassSubjectGrade.Grade,
                    'SubjectCode': class_subject_grade.Subject.SubjectCode
                }

                list_data_class_subject_grade.append(dict_class_subject_grade)
                unique_classes.add(class_name)

            sorted_unique_classes = sorted(unique_classes)
      
            # Return the list of class grades, the classes, and pagination information
            return jsonify({'result':list_data_class_subject_grade, 'count': total_count, 'classes': list(sorted_unique_classes)})
        else:
            return {'ClassSubjectGrade': [], 'Classes': [], 'currentPage': 1, 'totalPages': 0, 'totalItems': 0}

    except Exception as e:
        # Log the exception or handle it appropriately
        return None
    

def getStudentPerformance(str_student_id):
    try:
        list_student_performance = (
            db.session.query(StudentClassGrade, Class, Metadata)
            .join(Class, StudentClassGrade.ClassId == Class.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .filter(StudentClassGrade.StudentId == str_student_id)
            .order_by(desc(Metadata.Batch), desc(Metadata.Semester))
            .all()
        )

        if list_student_performance:
            list_performance_data = []  # Initialize a list to store dictionary data
            for gpa in list_student_performance:

                gpa_dict = {
                    'Grade': convertGradeToPercentage(gpa.StudentClassGrade.Grade),
                    'Semester': gpa.Metadata.Semester,
                    'Year': gpa.Metadata.Batch,
                }
                # Append the dictionary to the list
                list_performance_data.append(gpa_dict)

            # Check for missing entries
            batch_semester_map = {(gpa_dict["Year"], semester): False for semester in range(
                1, 4) for gpa_dict in list_performance_data}

            for gpa_dict in list_performance_data:
                batch_semester_map[(gpa_dict["Year"],
                                    gpa_dict["Semester"])] = True

            missing_entries = []
            for (batch, semester), is_present in batch_semester_map.items():
                if not is_present:
                    missing_entries.append({
                        "Year": batch,
                        "Grade": 0,
                        "Semester": semester
                    })

            # Append missing entries to list_performance_data
            list_performance_data.extend(missing_entries)

            # Sort the combined list based on year descending and semester descending
            sorted_list_performance_data = sorted(list_performance_data, key=lambda x: (
                x['Year'], x['Semester']), reverse=True)

            return sorted_list_performance_data
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def processGradeSubmission(file):
    try:
        # Check if the file is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        # Read the Excel file into a DataFrame
        df = pd.read_excel(file)
        
        list_finalized_grade = []
        is_some_submitted = False
        # Now you can access and manipulate the data in the DataFrame
        # For example, you can iterate through rows and access columns like this:
        for index, row in df.iterrows():
            # Extract the values from the DataFrame
            student_number = row['Student Number'] # OK
            student_name = row['Student Name']
            section_code = row['Section Code']
            subject_code = row['SubjectCode'] # OK
            semester = row['Semester'] # OK
            grade = row['Grade']
            batch = row['Batch'] # OK
            
            # Split the section_code by the last space and keep the first part
            course_code = section_code.rsplit(' ', 1)[0] 
            
            # Split the section_code by space, get the last part, and split it by hyphen '-' to extract year and section
            year, section = section_code.split(' ')[-1].split('-')
            print("BEFORE")
            # Now you can use the modified_section_code as needed in your code
            student_data = (
                db.session.query(Student,  StudentClassSubjectGrade, ClassSubject, Class, Subject, Course, Metadata)
                .join(StudentClassSubjectGrade, StudentClassSubjectGrade.StudentId == Student.StudentId)
                .join(ClassSubject, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId)
                .join(Class, Class.ClassId == ClassSubject.ClassId)
                .join(Metadata, Metadata.MetadataId == Class.MetadataId)
                .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
                .join(Course, Course.CourseId == Metadata.CourseId)
                .filter(Student.StudentNumber == student_number, Metadata.Year == year, Class.Section == section, Metadata.Batch == batch, Metadata.Semester == semester,  Subject.SubjectCode == subject_code)
                .order_by(desc(Student.Name), desc(Metadata.Year), desc(Class.Section), desc(Metadata.Batch))
                .first()
            )
            if(student_data.Class.IsGradeFinalized==False):
                # Check if grade is int
                # Print the type of grade
                print("TYPE: ", type(grade))
                
                
                if isinstance(grade, int) or isinstance(grade, float):
                    if grade <= 3: # PASSED
                        student_data.StudentClassSubjectGrade.Grade = grade
                        student_data.StudentClassSubjectGrade.AcademicStatus = 1
                        db.session.add(student_data.StudentClassSubjectGrade)
                        is_some_submitted = True
                    elif grade > 3 and grade <= 5: # FAILED
                        student_data.StudentClassSubjectGrade.Grade = grade
                        student_data.StudentClassSubjectGrade.AcademicStatus = 2
                        db.session.add(student_data.StudentClassSubjectGrade)
                        is_some_submitted = True
                else:
                    if grade == "Inc" or grade == 'Incomplete' or grade == "I": # WITHDRAWN
                        student_data.StudentClassSubjectGrade.AcademicStatus = 3
                        # Update grade to 0
                        student_data.StudentClassSubjectGrade.Grade = 0
                        db.session.add(student_data.StudentClassSubjectGrade)
                        is_some_submitted = True
                    else: # DROPOUT
                        student_data.StudentClassSubjectGrade.AcademicStatus = 4
                        # Update grade
                        student_data.StudentClassSubjectGrade.Grade = 0
                        db.session.add(student_data.StudentClassSubjectGrade)
                        is_some_submitted = True
            else:
                # Append the object to list_finalized_grade
                list_finalized_grade.append({
                    "StudentNumber": student_number,
                    "StudentName": student_name,
                    "SectionCode": section_code,
                    "SubjectCode": subject_code,
                    "Semester": semester,
                    "Grade": grade,
                    "Batch": batch,
                    "Error": "Grade has been finalized already in class"
                })
        # If all data is updated successfully then commit the data
        db.session.commit()
        
        if list_finalized_grade and is_some_submitted:
            return jsonify({'error': 'Some data cannot be updated', 'errors': list_finalized_grade}), 400
        elif list_finalized_grade and is_some_submitted == True:
            return jsonify({'error': 'All data are already finalized', 'errors': list_finalized_grade}), 400
        else:
            return jsonify({'result': 'File uploaded and data processed successfully'}), 200

    except Exception as e:
        print("ERROR: ", e)
        return jsonify({'error': 'An error occurred while processing the file'}), 500
    
def getClassSubject(class_id):
    try:
        data_class_subject = (
            db.session.query(Class, Metadata, ClassSubject, Subject, ClassSubjectGrade, Course)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(ClassSubject, ClassSubject.ClassId == Class.ClassId)
            .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .join(ClassSubjectGrade, ClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .filter(ClassSubject.ClassId == class_id)
            .all()
        )

        if data_class_subject:
            # For loop the data_student and put it in dictionary
            list_class_subject = []
            for class_subject in data_class_subject:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_subject.Course.CourseCode} {class_subject.Metadata.Year}-{class_subject.Class.Section}"

                # Check if the class_subject.FacultyId exists, if yes, make a query for it
                if class_subject.ClassSubject.FacultyId or class_subject.ClassSubject.Schedule:
                    teacher_id = 0
                    if class_subject.ClassSubject.FacultyId:
                        teacher = db.session.query(Faculty).filter(Faculty.FacultyId == class_subject.ClassSubject.FacultyId).first()
                        if teacher:
                            teacher_id = teacher.FacultyId

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
                    'Batch': class_subject.Metadata.Batch if class_subject.Metadata else None,
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
        data_class_details = db.session.query(Class, Metadata, Course).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).filter(Class.ClassId == class_id).all()
        
        if data_class_details:
                # For loop the data_student and put it in dictionary
            for class_details in data_class_details:
                # Combine the course_code, year, section to class_name variable
                class_name = f"{class_details.Course.CourseCode} {class_details.Metadata.Year}-{class_details.Class.Section}"

                dict_class_details = {
                    "Course": class_details.Course.Name,
                    "Section Code": class_name,
                    'Batch': class_details.Metadata.Batch,
                    "Semester": class_details.Metadata.Semester
                }
                return jsonify({'data': dict_class_details})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    

# DOING HERE
def getStudentClassSubjectData(classSubjectId, skip, top, order_by, filter):
    try:
        print('skip, top, order_by, filter: ', skip, top, order_by, filter)
        data_class_details = db.session.query(ClassSubject).filter_by(ClassSubjectId = classSubjectId).first()
        
        # Get the StudentClassSubjectGrade
        if data_class_details:
            data_student_subject_grade_query = db.session.query(StudentClassSubjectGrade, Student).join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId)
            
            # Default filter
            # .filter(StudentClassSubjectGrade.ClassSubjectId == data_class_details.ClassSubjectId).all()
            
            filter_conditions = []
            
            filter_conditions.append(
                StudentClassSubjectGrade.ClassSubjectId == classSubjectId
            )
            
            if filter:
                filter_parts = filter.split(' and ')
                for part in filter_parts:
                    
                    # Check if part has to lower in value
                    if '(tolower(' in part:
                        # Extracting column name and value
                        column_name = part.split("(")[3].split("),'")[0]
                        value = part.split("'")[1]
                        # print column name and value
                        print('column_name, value: ', column_name, value)
                        column_str = None
                        if column_name.strip() == 'StudentNumber':
                            column_str = getattr(Student, 'StudentNumber')
                        elif column_name.strip() == 'Name':
                            column_str = getattr(Student, 'Name')
                        elif column_name.strip() == 'Email':
                            column_str =  getattr(Student, 'Email')     
                            
                        if column_str:
                            # Append column_str
                            filter_conditions.append(
                                func.lower(column_str).like(f'%{value}%')
                            )
                    else:
                        # column_name = part[0][1:]  # Remove the opening '('
                        column_name, value = [x.strip() for x in part[:-1].split("eq")]
                        column_name = column_name[1:]
                        
                        # print column name and value
                        print('column_name, value: ', column_name, value)
                        
                        column_num = None
                        int_value = value.strip(')')
                
                        if column_name.strip() == 'Grade':
                            column_num = StudentClassSubjectGrade.Grade
                        
                            filter_conditions.append(
                                column_num == int_value
                            )
                            
            filter_query = data_student_subject_grade_query.filter(and_(*filter_conditions))
            
            if order_by:
                # Determine the order attribute
                if order_by.split(' ')[0] == 'StudentNumber':
                    order_attr = getattr(Student, 'StudentNumber')
                elif order_by.split(' ')[0] == "Name":
                    order_attr = getattr(Student, 'Name')
                elif order_by.split(' ')[0] == 'Email':
                    order_attr = getattr(Student, 'Email')
                elif order_by.split(' ')[0] == 'Grade':
                    order_attr = getattr(StudentClassSubjectGrade, 'Grade')
                else:
                    order_attr = getattr(StudentClassSubjectGrade, 'DateEnrolled')
    
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
            else:
                # Apply default sorting
                order_query = filter_query.order_by(desc(Student.StudentNumber))
        
        
            # Query for counting all records
            total_count = order_query.count()
            # Limitized query = 
            student_limit_offset_query = order_query.offset(skip).limit(top).all()
            
            if student_limit_offset_query:
                list_student_data = []
                    # For loop the data_student and put it in dictionary
                for student_subject_grade in student_limit_offset_query:
                    dict_student_subject_grade = {
                        'DateEnrolled': student_subject_grade.StudentClassSubjectGrade.DateEnrolled,
                        "ClassSubjectId": student_subject_grade.StudentClassSubjectGrade.ClassSubjectId,
                        "StudentId": student_subject_grade.Student.StudentId,
                        "StudentNumber": student_subject_grade.Student.StudentNumber,
                        "Name": student_subject_grade.Student.Name,
                        "Email": student_subject_grade.Student.Email,
                        "Grade": student_subject_grade.StudentClassSubjectGrade.Grade
                    }
                    list_student_data.append(dict_student_subject_grade)
                return  jsonify({'result': list_student_data, 'count': total_count}), 200
            else:
                return jsonify({'result': [], 'count': 0})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def deleteClassSubjectStudent(class_subject_id, student_id):
    try:
        student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(ClassSubjectId = class_subject_id, StudentId = student_id).first()
        # Find class_subject
        class_subject = db.session.query(ClassSubject).filter_by(ClassSubjectId = class_subject_id).first()
        # Find the class_subject with same ClassId
        class_subjects = db.session.query(ClassSubject).filter_by(ClassId = class_subject.ClassId).all()
        # for loop the class_subjects and count the amount of subject of student
        total_subjects = 0
        
        # Get Class
        class_data = db.session.query(Class).filter_by(ClassId = class_subject.ClassId).first()
        
        # Check if grade is already finalized
        if class_data.IsGradeFinalized:
            return jsonify({'success': False, 'error': 'Cannot delete student because the grade is already finalized'}), 400
        
        for class_subject in class_subjects:
            student_class_subject_grade_data = db.session.query(StudentClassSubjectGrade).filter_by(ClassSubjectId = class_subject.ClassSubjectId, StudentId = student_id).first()
            if student_class_subject_grade_data:
                total_subjects += 1
                if total_subjects == 2:
                    break
                
        if student_class_subject_grade:
            if total_subjects == 1:
                # Delete the student_class_grade:
                student_class_grade = db.session.query(StudentClassGrade).filter_by(ClassId = class_subject.ClassId, StudentId = student_id).first()
                db.session.delete(student_class_grade)
            
            db.session.delete(student_class_subject_grade)
            db.session.commit()
            return jsonify({'success': True, 'result': 'Data deleted successfully'}), 200
        else:
            return jsonify({'error': 'Data cannot be deleted'})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    # getCurriculumSubject


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
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e}), 500

def getCurriculumData(skip, top, order_by, filter):
    try:
        
        metadata_query = (
            db.session.query(Curriculum, Metadata, Course, Subject)
            .join(Metadata, Metadata.MetadataId == Curriculum.MetadataId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .join(Subject, Subject.SubjectId == Curriculum.SubjectId)
        )
        
        # metadata_query = db.session.query(Curriculum, Metadata, Course, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(Subject, Subject.SubjectId == Curriculum.SubjectId)
        # DEFAULT ORDER BY
        # .order_by(desc(Metadata.Batch), desc(Metadata.Year)).all()
        
        filter_conditions = []
        # Split filter string by 'and'
        # append the str_teacher_id
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    # Extracting column name and value
                    column_name = part.split("(")[3].split(")")[0]
                    value = part.split("'")[1]
                    column_str = None
                    
                    if column_name.strip() == 'CourseCode':
                        column_str = getattr(Course, 'CourseCode')
                    elif column_name.strip() == 'SubjectCode':
                        column_str = getattr(Subject, 'SubjectCode')
                    elif column_name.strip() == 'Subject':
                        column_str =  getattr(Subject, 'Name')     
                 
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

                    if not int_value.isdigit():
                        int_value = 0
                    
                    if column_name.strip() == 'Year':
                        column_num = Metadata.Year
                    elif column_name.strip() == 'Batch':
                        column_num = Metadata.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = Metadata.Semester
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                    
        filter_query = metadata_query.filter(and_(*filter_conditions))
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'CourseCode':
                order_attr = getattr(Course, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == "SubjectCode":
                order_attr = getattr(Subject, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Subject':
                order_attr = getattr(Subject, 'Name')
            elif order_by.split(' ')[0] == 'Year':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
           
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.Year))
        
        
        # Query for counting all records
        total_count = order_query.count()
        # Limitized query = 
        metadata_limit_offset = order_query.offset(skip).limit(top).all()

       
        
        # Get the StudentClassSubjectGrade
        if metadata_limit_offset:
            list_metadata = []
                # For loop the data_student and put it in dictionary
            for data in metadata_limit_offset:
                # Convert the Year to 1st, 2nd, 3rd, 4th
                dict_metadata = {
                    "CurriculumId": data.Curriculum.CurriculumId,
                    "MetadataId": data.Metadata.MetadataId,
                    "Year": data.Metadata.Year,
                    "Semester": data.Metadata.Semester,
                    "Batch": data.Metadata.Batch,
                    "CourseCode": data.Course.CourseCode,
                    "Subject": data.Subject.Name,
                    "SubjectCode": data.Subject.SubjectCode
                }
                list_metadata.append(dict_metadata)
            return jsonify({'result': list_metadata, 'count': total_count})

        else:
            print("NO METADA FOUND")
            return jsonify({'result': [], 'count': 0})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def getCurriculumOptions():
    try:
      # Get all unique SubjectCode and CourseCode
        unique_subject_code = db.session.query(Subject).all()
        unique_course_code = db.session.query(Course).all()
        
        if not unique_subject_code:
            return jsonify({'error': 'No subject found'}), 400
        elif not unique_course_code:
            return jsonify({'error': 'No course found'}), 400
        else:
            year_options = []
            batch_options = []
            semester_options = []
            course_options = []
            subject_options = []
            
            current_year = datetime.now().year
            previous_year = current_year - 1
            future_year = current_year + 1
            
            # Options for frontend
            year = [1, 2, 3, 4]
            batch = [previous_year , current_year, future_year]
            semesters = [1, 2, 3]
            
            
            for y in year:
                year_dict = {
                    "Year": y
                }
                year_options.append(year_dict)
                
            for b in batch:
                batch_dict = {
                    "Batch": b
                }
                batch_options.append(batch_dict)
            
            for s in semesters:
                semester_dict = {
                    "Semester": s
                }
                semester_options.append(semester_dict)
            
            for c in unique_course_code:
                course_dict = {
                    "CourseCode": c.CourseCode
                }
                course_options.append(course_dict)
                
            for s in unique_subject_code:
                subject_dict = {
                    "SubjectCode": s.SubjectCode + ' - ' + s.Name
                }
                subject_options.append(subject_dict)
            
            # Return all options
            return jsonify({'result': {'yearOptions': year_options, 'subjectCodeOptions': subject_options, 'batchOptions': batch_options, 'courseOptions': course_options, 'semesterOptions': semester_options}})
        
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e})
    

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
        active_teacher = db.session.query(Faculty).filter_by(is_active = True).all()
        # Get the StudentClassSubjectGrade
        if active_teacher:
            list_active_teacher = []
                # For loop the active_teacher and put it in dictionary
            for data in active_teacher:
                middle_name = data.middle_name if data.middle_name else ""
                full_name = f"{data.last_name}, {data.first_name} {middle_name}"
                
                dict_active_teacher = {
                    "TeacherId": data.FacultyId,
                    "TeacherName": full_name,
                }
                list_active_teacher.append(dict_active_teacher)
            return  jsonify({'data': list_active_teacher})
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
    
    
def processAddingCurriculumSubjects(data, excelType=False):
    # MANUAL ADDING DATA
    if excelType == False:
        # print("DATA: ", data,Cours)
        course_code = data['CourseCode']
        subject_code = data['SubjectCode']
        year_level = data['Year']
        semester = data['Semester']
        batch = data['Batch']
        
        if ' - ' in subject_code:
            # Split and get the 1st element
            subject_code = subject_code.split(' - ')[0]
        
        course = db.session.query(Course).filter_by(CourseCode = course_code).first()
                
        # Check if course existing
        if not course:
            
            print("INVALID COURSE")
            # Return cannot added data. Course already exist
            return jsonify({'error': 'Invalid Course'}), 400
        else:
            # Check if already have classes and avoid adding curriculum.
            class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch, Metadata.CourseId == course.CourseId).first()
            if class_data:
                # Return cannot added data. Class already exist
                return jsonify({'error': 'Cannot add subject curriculum has already class existing.'}), 400
            
            metadata = db.session.query(Metadata).filter_by(Year = year_level, Semester = semester, Batch = batch, CourseId = course.CourseId).first()
            # Check if have a class already with yhe same year_level, semester, batch and course id
            if metadata:
                # Check if subject is existing
                subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()
                
                
                if subject:
                    # Check if Curriculum is existing
                    curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Metadata.CourseId == course.CourseId, Subject.SubjectCode == subject_code, Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                    
                    # If no curriculum subject exist then create curriculum
                    if not curriculum_subject_exist:
                        # Create a curriculum
                        new_curriculum = Curriculum(
                            MetadataId=metadata.MetadataId,
                            SubjectId=subject.SubjectId
                        )
                    
                        db.session.add(new_curriculum)
                        db.session.commit()                        
                        
                        dict_subject = subject.to_dict()
                        
                        print('dict_subject:: ', dict_subject)
                        
                        # Return data added successfully
                        return jsonify({'success': 'Data added successfully'}), 200
                    else:
                        # Return cannot added data. Curriculum already exist
                        return jsonify({'error': 'Curriculum already exist'}), 400
                else:
                    # Return cannot added data. Invalid Subject Code
                    return jsonify({'error': 'Invalid Subject Code'}), 400
            else:
                # Check if subject is existing
                subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()   
        
                new_metadata = Metadata(
                    CourseId=course.CourseId,
                    Year=year_level,
                    Semester=semester,
                    Batch=batch
                )
                    
                db.session.add(new_metadata)
                db.session.flush()
                                                    
                if subject:                       
                    curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Subject.SubjectCode == subject_code, Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                        
                    if not curriculum_subject_exist:
                        # Create a curriculum
                        new_curriculum = Curriculum(
                            MetadataId=new_metadata.MetadataId,
                            SubjectId=subject.SubjectId
                        )
                
                        db.session.add(new_curriculum)
                        db.session.commit()
                        
                        dict_subject = subject.to_dict()
                        
                        # Return data added successfully
                        return jsonify({'success': 'Data added successfully', 'SubjectName': dict_subject['Name']}), 200
                    else:
                        # Return cannot added data. Curriculum already exist
                        return jsonify({'error': 'Already exist'}), 400
                    
                else:
                    # Return cannot added data. Invalid Subject Code
                    return jsonify({'error': 'Invalid Subject Code'}), 400
            
    # EXCEL TYPE
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
        list_curriculum_subjects = []
        errors = []
        
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
                errors.append({
                    "Course": course_code,
                    "Subject Code": subject_code,
                    "Year": year_level,
                    "Semester": semester,
                    "Batch": batch,
                    "Error": "Invalid Course"
                })
            else:
                # Check if already have classes and avoid adding curriculum.
                class_data = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch, Metadata.CourseId == course.CourseId).first()
                if class_data:
                    errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Curriculum has already class existing"
                    })
                    # Go to next for loop
                    continue
                
                metadata = db.session.query(Metadata).filter_by(Year = year_level, Semester = semester, Batch = batch, CourseId = course.CourseId).first()
                
                if metadata:
                    # Check if subject is existing
                    subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()
                    
                    if subject:
                        # Check if Curriculum is existing
                        curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Metadata.CourseId == course.CourseId, Subject.SubjectCode == subject_code, Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                        if not curriculum_subject_exist:
                            # Create a curriculum
                            new_curriculum = Curriculum(
                                MetadataId=metadata.MetadataId,
                                SubjectId=subject.SubjectId
                            )
                        
                            db.session.add(new_curriculum)
                            db.session.commit()
                            
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
                            db.session.rollback()
                            errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Curriculum subject already exist"
                            })
                            
                            
                    else:
                        db.session.rollback()
                        errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Invalid Subject Code"
                        })
                        
                else: # NO META DATA FIELD
                    # Check if subject is existing
                    subject = db.session.query(Subject).filter_by(SubjectCode = subject_code).first()   
            
                    new_metadata = Metadata(
                        CourseId=course.CourseId,
                        Year=year_level,
                        Semester=semester,
                        Batch=batch
                    )
                        
                    db.session.add(new_metadata)
                    db.session.flush()
                                                        
                    if subject:                       
                        curriculum_subject_exist = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Subject.SubjectCode == subject_code, Metadata.Year == year_level, Metadata.Semester == semester, Metadata.Batch == batch).first()
                            
                        if not curriculum_subject_exist:
                            # Create a curriculum
                            new_curriculum = Curriculum(
                                MetadataId=new_metadata.MetadataId,
                                SubjectId=subject.SubjectId
                            )
                    
                            db.session.add(new_curriculum)
                            db.session.commit()
                            
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
                            db.session.rollback()
                            errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Already exist"
                            })
                        
                    else:
                        db.session.rollback()
                        errors.append({
                                "Course": course_code,
                                "Subject Code": subject_code,
                                "Year": year_level,
                                "Semester": semester,
                                "Batch": batch,
                                "Error": "Invalid Subject Code"
                        })
                    
            
        if errors and not list_curriculum_subjects:
            return jsonify({'error': 'Something went wrong. The data could not be processed successfully.', 'errors': errors}), 500
        if errors and list_curriculum_subjects:
            return jsonify({'warning': 'Some data added successfully', 'errors': errors, 'data': list_curriculum_subjects}), 500
        else:
            db.session.commit()
            return  jsonify({'result': 'Data added successfully', 'data': (list_curriculum_subjects)}), 200
        
        
def deleteCurriculumSubjectData(curriculumId):
    try:
      # Get curriculum
        curriculum = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Curriculum.CurriculumId == curriculumId).first()
      
        if curriculum:
            print("EXIST")
            # Find a class that has the same metadata value which is CourseId, Year, Semester, Batch
            class_data = db.session.query(Class).filter_by(CourseId = curriculum.Metadata.CourseId, Year = curriculum.Metadata.Year, Semester = curriculum.Metadata.Semester, Batch = curriculum.Metadata.Batch).first()
            
            if class_data:
                return jsonify({'error': 'Cannot delete subject. Already have class existing'}), 400
            else:
                # Delete the metadata 
                db.session.delete(curriculum.Metadata)
                db.session.commit()
                return jsonify({'result': 'Data deleted successfully'}), 200
        else:
            return jsonify({'error': 'Data cannot be deleted'}), 400
        
    except Exception as e:
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
      

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


def processAddingStudentInSubject(data, class_subject_id, excelType=False):
    try:
        if excelType:
            if data.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            if not data.filename.endswith(('.xlsx', '.xls')):
                return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

            df = pd.read_excel(data)
            list_students_added = []
            
            # list_student_graduate = []
            errors = []

            class_subject = db.session.query(ClassSubject).filter_by(ClassSubjectId = class_subject_id).first()

             # Get the class
            class_data = db.session.query(Class).filter_by(ClassId = class_subject.ClassId).first()
            # Check if grade is already finalized
            if class_data.IsGradeFinalized:
                return jsonify({'error': True, 'errorLast': 'Cannot add student. Grade is already finalized'}), 400
            
            if class_subject:

                for index, row in df.iterrows():
                    # find class_subject_id
                    student_number = str(row['Student Number'])
                    student_date_enrolled = row['Date Enrolled']
                    
                    if not student_number:
                        errors.append({
                            'StudentNumber': 'N/A',
                            'DateEnrolled': student_date_enrolled,
                            'Error': 'Student Number must have a value'
                        })
                        continue
                    
                    if student_date_enrolled:
                        if isinstance(student_date_enrolled, datetime):
                            student_date_enrolled = student_date_enrolled.strftime("%Y-%m-%d")
                        else:
                            errors.append({
                                'StudentNumber': student_number,
                                'DateEnrolled': "N/A",
                                'Error': 'Invalid Date Enrolled format'
                            })
                            continue
                    
                    if not student_date_enrolled:
                        errors.append({
                            'StudentNumber': student_number,
                            'DateEnrolled': 'N/A',
                            'Error': 'Date Enrolled must have a value'
                        })
                        continue
                    
                
                    student = db.session.query(Student).filter_by(StudentNumber = student_number).first()
                
                    if student:
                        student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId = student.StudentId, ClassSubjectId = class_subject_id).first()
                        
                        if student_class_subject_grade:
                            errors.append({
                                'StudentNumber': student_number,
                                'DateEnrolled': student_date_enrolled,
                                'Error': 'Student already exist in the subject'
                            })
                        else:
                            # Check if student has already studentClassGrade
                            student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId = student.StudentId, ClassId = class_subject.ClassId).first()
                            if not student_class_grade:
                                # Create StudentClassGrade
                                new_student_class_grade = StudentClassGrade(
                                    StudentId=student.StudentId,
                                    ClassId=class_subject.ClassId,
                                    Grade=0.00
                                )
                                
                                db.session.add(new_student_class_grade)
                                db.session.flush()
                            
                            # Create StudentClassSubjectGrade
                            new_student_class_subject_grade = StudentClassSubjectGrade(
                                StudentId=student.StudentId,
                                ClassSubjectId=class_subject_id,
                                DateEnrolled=student_date_enrolled,
                                Grade=0.00
                            )
                            
                            db.session.add(new_student_class_subject_grade)
                            db.session.commit()
                            
                            dict_student_class_subject_grade = {
                                "ClassSubjectId": class_subject_id,
                                "StudentId": student.StudentId,
                                "StudentNumber": student.StudentNumber,
                                "Name": student.Name,
                                "Email": student.Email,
                                "Grade": new_student_class_subject_grade.Grade
                            }

                            # append the list_students_added
                            list_students_added.append(dict_student_class_subject_grade)
                    else:
                        # Append in errors
                        errors.append({
                            'StudentNumber': student_number,
                            'DateEnrolled': student_date_enrolled,
                            'Error': 'Student Number does not exist'
                        })
                        
                if errors and len(list_students_added) > 0:
                    db.session.rollback()
                    return jsonify({'warning': 'Some data added successfully', 'errors': errors, 'data': list_students_added}), 500
                elif errors and len(list_students_added) == 0:
                    db.session.rollback()
                    return jsonify({'error': 'Adding the data failed', 'errors': errors}), 500
                else:
                    return jsonify({'result': 'Data added successfully', 'data': list_students_added}), 200
            else:
                return jsonify({'error': 'Class Subject does not exist'}), 400
            
        else:
            # Get the data.StudentNumber and DateEnrolled
            student_number = data['StudentNumber']
            student_date_enrolled = data['DateEnrolled']
            
            # Check if student numberhave value and remove unecessary spaces
            if not student_number:
                return jsonify({'error': 'Student Number must have a value'}), 400
            else:
                student_number = student_number.strip()
            
            # Convert student_date_enrolled to date format
            if student_date_enrolled is not None:
                try:
                    # Adjust the format string to include the time component
                    student_date_enrolled = datetime.strptime(student_date_enrolled, "%Y-%m-%dT%H:%M:%S.%fZ")
                    
                    # Extract only the date part
                    student_date_enrolled = student_date_enrolled.date()
                    
                    print('student_date_enrolled: ', student_date_enrolled)
                except Exception as e:
                    return jsonify({'error': 'Invalid Date Enrolled format'}), 400
            
            # Find class_subject_id
            class_subject = db.session.query(ClassSubject).filter_by(ClassSubjectId = class_subject_id).first()
            # Check if not class_subject then return
            if not class_subject:
                return jsonify({'error': 'Class Subject does not exist'}), 400
            
            # Get the class
            class_data = db.session.query(Class).filter_by(ClassId = class_subject.ClassId).first()
            # Check if grade is already finalized
            if class_data.IsGradeFinalized:
                return jsonify({'error': 'Cannot add student. Grade is already finalized'}), 400
            
            # Check if student_number is existing
            student = db.session.query(Student).filter_by(StudentNumber = student_number).first()
            if student:
                # Check if student has already studentClassSubjectGrade
                student_class_subject_grade = db.session.query(StudentClassSubjectGrade).filter_by(StudentId = student.StudentId, ClassSubjectId = class_subject_id).first()
                if student_class_subject_grade:
                    return jsonify({'error': 'Student already exist in the subject'}), 400
                else:
                    # Check if student has already studentClassGrade
                    student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId = student.StudentId, ClassId = class_subject.ClassId).first()
                    if not student_class_grade:
                        # Create StudentClassGrade
                        new_student_class_grade = StudentClassGrade(
                            StudentId=student.StudentId,
                            ClassId=class_subject.ClassId,
                            Grade=0.00
                        )
                        
                        db.session.add(new_student_class_grade)
                        db.session.flush()
                    
                    # Create StudentClassSubjectGrade
                    new_student_class_subject_grade = StudentClassSubjectGrade(
                        StudentId=student.StudentId,
                        ClassSubjectId=class_subject_id,
                        DateEnrolled=student_date_enrolled,
                        Grade=0.00
                    )
                    
                    db.session.add(new_student_class_subject_grade)
                    db.session.commit()
                    
                    dict_student_class_subject_grade = {
                        "ClassSubjectId": class_subject_id,
                        "StudentId": student.StudentId,
                        "StudentNumber": student.StudentNumber,
                        "Name": student.Name,
                        "Email": student.Email,
                        "Grade": new_student_class_subject_grade.Grade
                    }
                    
                    return jsonify({'success': True, 'message': "Successfully"})
            else:
                return jsonify({'error': 'Student Number does not exist'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
 
def getMetadata(skip, top, order_by, filter):
    try:
        
        metadata_query = db.session.query(Metadata, Course).join(Course, Course.CourseId == Metadata.CourseId).distinct(Course.CourseCode, Course.Name, Metadata.Batch, Metadata.Semester)
        
        # Order default
        # .order_by(desc(Metadata.Batch), desc(Metadata.Semester))


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
                    
                    if column_name.strip() == 'CourseCode':
                        column_str = getattr(Course, 'CourseCode')
                    elif column_name.strip() == 'Course':
                        column_str = getattr(Course, 'Name')
                 
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
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = metadata_query.filter(and_(*filter_conditions))
        
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'CourseCode':
                print('IN COURSE CODE')
                order_attr = getattr(Course, 'CourseCode')
            elif order_by.split(' ')[0] == "Course":
                order_attr = getattr(Course, 'Name')
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(Metadata, 'Batch')
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, 'Semester')           
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                print("IN QUERY")
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Metadata.Batch), desc(Metadata.Semester))
            # order params
            

        metadata_main_query = order_query.offset(skip).limit(top).all()
        total_count = order_query.count()

        list_metadata = []
        if metadata_main_query:
            for data in metadata_main_query:
                # Check data.Course.Name, data.Metadata.Batch and data.Metadata.Semester if exist in list_metadata
                # Find a class that has the same MetadataId
                class_data = db.session.query(Class).filter_by(MetadataId=data.Metadata.MetadataId).first()

                # Check if class_data exists
                if class_data:
                    # Set IsGradeFinalized to its value if it exists, else set it to None
                    is_grade_finalized = class_data.IsGradeFinalized if hasattr(class_data, 'IsGradeFinalized') else None
                else:
                    # Set to None if class_data doesn't exist
                    is_grade_finalized = None

                # Create a dict
                dict_metadata = {
                    'MetadataId': data.Metadata.MetadataId,
                    'Course': data.Course.Name,
                    'CourseCode': data.Course.CourseCode,
                    'Semester': data.Metadata.Semester,
                    'Batch': data.Metadata.Batch,
                    'IsGradeFinalized': is_grade_finalized
                }

                # Append the dict to the list_metadata
                list_metadata.append(dict_metadata)
            
            return jsonify({'result': list_metadata, 'count': total_count})
        else:
            return jsonify({'result': None})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))


def finalizedGradesReport(metadata_id):
    try:
        data_metadata = db.session.query(Metadata, Course).join(Course, Course.CourseId == Metadata.CourseId).filter(Metadata.MetadataId == metadata_id).first()
        
        
        
        # print('data_metadata: ', data_metadata)
        if data_metadata:
            # Select class that has the same Batch, Semester and Course
            data_course_class = db.session.query(Class, Metadata, Course).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).filter(Metadata.Batch == data_metadata.Metadata.Batch, Metadata.Semester == data_metadata.Metadata.Semester, Metadata.CourseId == data_metadata.Course.CourseId).order_by(Metadata.Year, Class.Section).all()
            # if data class 
            if data_course_class:
                student_class_grade_list = [] # For list of grade in class subject (Object - Lister, StudentId, ClassId etc...)

                course_grade_list = [] # Class grade lisst to calculate course grade
                
                student_list = [] # For checking of student if graduated
                list_class = [] # For class list that will be reiterated
                list_grade_analytics_details = [] # For details of analytics (Lister, Passed, Failed, Incomplete etc.)
                
                # Get count of subject with the same metadata
                count_subject = db.session.query(Curriculum).filter_by(MetadataId = metadata_id).count()
        
                # for loop the data_class and make a dictionary and append to the list_class
                for course_class_data in data_course_class:
                    dict_class = {
                        'ClassId': course_class_data.Class.ClassId,
                        'CourseId': course_class_data.Metadata.CourseId,
                        'Section': course_class_data.Class.Section,
                        'Course': course_class_data.Course.CourseCode,
                        'Year': course_class_data.Metadata.Year,
                        'Semester': course_class_data.Metadata.Semester,
                        'Batch': course_class_data.Metadata.Batch,
                        'SubjectCount': count_subject
                    }
                    # Append th list_class
                    list_class.append(dict_class)

                    # Make a course grade data for CourseId, Batch, Semester, Grade and Grades Array for storing all grades
                    course_grade_data = {
                        'CourseId': course_class_data.Metadata.CourseId,
                        'Batch': course_class_data.Metadata.Batch,
                        'Semester': course_class_data.Metadata.Semester,
                        'Grade': 0.00,
                        'Grades': []
                    }
                
                if list_class:
                    
                    # for loop it
                    for class_data in list_class:
                        # Get the class_subject
                        print('class_data: ', class_data)
                        # Get Class data and update IsGradeFinalized
                        class_data_update = db.session.query(Class).filter_by(ClassId = class_data['ClassId']).first()
                        class_data_update.IsGradeFinalized = True
                        
                        data_class_subject = db.session.query(ClassSubject, Subject).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).filter(ClassSubject.ClassId == class_data['ClassId']).all()
                        # data_class_subject = db.session.query(ClassSubject, Subject, Faculty).join(Subject, Subject.SubjectId == ClassSubject.SubjectId).join(Faculty, Faculty.TeacherId == ClassSubject.TeacherId).filter(ClassSubject.ClassId == class_data['ClassId']).all()

                        
                        list_class_subject = []
                        
                        if data_class_subject:
                            # for loop the data_class_subject and make a dictionary and append to the list_class_subject
                            for class_subject in data_class_subject:
                                # print('===============================================================================================================================================: ')
                                dict_class_subject = {
                                    'ClassSubjectId': class_subject.ClassSubject.ClassSubjectId,
                                    'SubjectCode': class_subject.Subject.SubjectCode,
                                    'Subject': class_subject.Subject.Name,
                                    'Schedule': class_subject.ClassSubject.Schedule
                                }
                                
                                # Make a dict_class_subject_grade
                                dict_grade_data_list = {
                                    'ClassSubjectId': class_subject.ClassSubject.ClassSubjectId,
                                    'ClassId': class_subject.ClassSubject.ClassId,
                                    'StudentId': [],
                                    'StudentClassSubjectGrade': [],
                                    'Grade': 0,
                                    'Passed': 0,
                                    'Failed': 0,
                                    'Incomplete': 0,
                                    'Dropout': 0,
                                    'PresidentsLister': 0,
                                    'DeansLister': 0
                                }
                                
                                
                                # Append the list_class_subject
                                list_class_subject.append(dict_class_subject)
                                # Get all student in the classSubject with the same classId
                                data_student_class_subject_grade = db.session.query(StudentClassSubjectGrade, Student).join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId).filter(StudentClassSubjectGrade.ClassSubjectId == class_subject.ClassSubject.ClassSubjectId).all()
                                
                                # Additional details for generating report for analytics (Passed, Failed, PresidentLister, DeansLister)
                                if data_student_class_subject_grade:
                                    for student_class_subject_grade in data_student_class_subject_grade:
                                        
                                        
                                        current_student_id = student_class_subject_grade.Student.StudentId
                                        current_grade = student_class_subject_grade.StudentClassSubjectGrade.Grade
                                        # Get academic status
                                        academic_status = student_class_subject_grade.StudentClassSubjectGrade.AcademicStatus
                                        
                                        if academic_status == 1:
                                            dict_grade_data_list['Passed'] += 1
                                        elif academic_status == 2:
                                            dict_grade_data_list['Failed'] += 1
                                        elif academic_status == 3:
                                            dict_grade_data_list['Incomplete'] += 1
                                        elif academic_status == 4:
                                            dict_grade_data_list['Dropout'] += 1
                                            
                                        # Append StudentId
                                        dict_grade_data_list['StudentId'].append(current_student_id)
                                        

                                        if current_grade != 0: 
                                            dict_grade_data_list['StudentClassSubjectGrade'].append(current_grade)
                                            # Check if an entry with the same StudentId already exists in student_class_grade_list
                                            found_entry = next((entry for entry in student_class_grade_list if entry["StudentId"] == current_student_id), None)
                                            
                                            if found_entry:
                                                # If an entry with the same StudentId exists, append the grade to the existing entry
                                                found_entry["Grade"].append(current_grade)
                                            else:
                                                # If no entry with the same StudentId exists, add a new entry to student_class_grade_list
                                                student_class_grade_list.append({
                                                    "StudentId": current_student_id,
                                                    "ClassId": class_subject.ClassSubject.ClassId,
                                                    "Grade": [current_grade],
                                                    # "IsGradeCompleted": True,
                                                    "Lister": 0
                                                })
                                                
                                        # else:
                                        #     # Check if an entry with the same StudentId already exists in student_class_grade_list
                                        #     found_entry = next((entry for entry in student_class_grade_list if entry["StudentId"] == current_student_id), None)
                                            
                                        #     if found_entry:
                                        #         # If an entry with the same StudentId exists, append the grade to the existing entry
                                        #         found_entry["IsGradeCompleted"] = False
                                        #     else:
                                        #         # If no entry with the same StudentId exists, add a new entry to student_class_grade_list
                                        #         student_class_grade_list.append({
                                        #             "StudentId": current_student_id,
                                        #             "ClassId": course_class_data.Class.ClassId,
                                        #             "Grade": [],
                                        #             "IsGradeCompleted": False,
                                        #             "Lister": 0
                                        #         })
                                        
                                    list_grade_analytics_details.append(dict_grade_data_list)
                            # Append the list_class_subject to the class_data
                            class_data['ClassSubject'] = list_class_subject
                            
                        else:
                            class_data['ClassSubject'] = None
                    # print('ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ: ')
                    # For caclculating the student overall grade
                    
                    for data in student_class_grade_list:
                        print("=================================================================================")
                        print("CLS GRADE (BEFORE CONVERT): ", data)
                        # append stundet id
                        student_list.append(data['StudentId'])
                        # Check the length of grade if more than or equal to 1
                        if len(data['Grade']) >= 1:
                            # Check if any grade is 4.0, if yes, set Lister to 0
                            is_lister = 1
                        
                            if len(data['Grade']) != class_data['SubjectCount']:
                                is_lister = 0
                            
                            if any(grade  >= 2.75 for grade in data['Grade']) and is_lister != 0:
                                is_lister = 0
                                
                            sum_grade = sum(data['Grade'])
                            # Get the average grade
                            average_grade = sum_grade / len(data['Grade'])
                            # Update the Grade
                            data['Grade'] = average_grade
                            
                            # Check if sum grade is below 1.75
                            if average_grade <= 1.5 and is_lister != 0:
                                print("PRESIDENT")
                                data['Lister'] = 1
                            elif average_grade <= 1.75 and average_grade > 1.5 and is_lister != 0:
                                data['Lister'] = 2
                                print("DEAN")
                            
                            
                            # STUDENT CLASS GRADE - StudentId, ClassId, Grade, Lister
                            # Data for Student Class Grade Average
                            student_class_grade = db.session.query(StudentClassGrade).filter_by(StudentId = data['StudentId'], ClassId = data['ClassId']).first()
                            if student_class_grade:
                                db.session.query(StudentClassGrade).filter_by(StudentId = data['StudentId'], ClassId = data['ClassId']).update({
                                    'Grade': data['Grade'], 'Lister': data['Lister']
                                })
                                print("UPDATING LISTER: ", data['Lister'])
                            else:
                                # Create a student_class_grade
                                new_student_class_grade = StudentClassGrade(
                                    StudentId = data['StudentId'],
                                    ClassId = data['ClassId'],
                                    Grade = data['Grade'],
                                    Lister = data['Lister']
                                )
                                print("UPDATING LISTER: ", data['Lister'])
                                db.session.add(new_student_class_grade)
                                db.session.flush()
                        print("CLS GRADE (UPDATED): ", data)
                    
                    # print('/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////: ')
                    # In analyticcs we have already StudentId this can be used to track class subject grade?
                    class_grade_list = []
                    
                    for data in list_grade_analytics_details:
                        # print("DATA ANALYtICS: ", data)
                        # CLASS SUBJET GRADE - ClassSubjectId, Grade, (Passed, Failed, Incomplete Dropout)
                        # CLASS GRADE - ClassId, (DeansLister, PresidentsLister), Grade
                        
                        # Find the average of StudentClassSubjectGrade
                        if len(data['StudentClassSubjectGrade']) >= 1:
                            sum_grade = sum(data['StudentClassSubjectGrade'])
                            # Get the average grade rounded to 2 decimal places
                            average_grade = round(sum_grade / len(data['StudentClassSubjectGrade']), 2)
                            # Update the Grade
                            data['StudentClassSubjectGrade'] = average_grade
                        else:
                            data['StudentClassSubjectGrade'] = 0.00
                            
                        
                        # For loop the StudentId
                        for student_id in data['StudentId']:
                            # Check if student_id is in student_class_grade_list
                            found_entry = next((entry for entry in student_class_grade_list if entry["StudentId"] == student_id), None)
                            
                            if found_entry:
                                # Check if Lister is 1
                                if found_entry['Lister'] == 1:
                                    data['PresidentsLister'] += 1
                                elif found_entry['Lister'] == 2:
                                    # Print president
                                    data['DeansLister'] += 1
                            
                            else:
                                print("NOT FOUND")
                                
                        # Add it in database:
                        # Check if class_subject_grade is existing
                        class_subject_grade = db.session.query(ClassSubjectGrade).filter_by(ClassSubjectId = data['ClassSubjectId']).first()
                        # If yes update it with new values
                        if class_subject_grade:
                            db.session.query(ClassSubjectGrade).filter_by(ClassSubjectId = data['ClassSubjectId']).update({
                                'Grade': data['StudentClassSubjectGrade'],
                                'Passed': data['Passed'],
                                'Failed': data['Failed'],
                                'Incomplete': data['Incomplete'],
                                'Dropout': data['Dropout']
                            })
                        else:
                            # Create a class_subject_grade
                            new_class_subject_grade = ClassSubjectGrade(
                                ClassSubjectId = data['ClassSubjectId'],
                                Grade = data['StudentClassSubjectGrade'],
                                Passed = data['Passed'],
                                Failed = data['Failed'],
                                Incomplete = data['Incomplete'],
                                Dropout = data['Dropout']
                            )
                            
                            db.session.add(new_class_subject_grade)
                            db.session.flush()
                            
                        # Check if ClassId already exisitng in class_grade_list
                        found_entry = next((entry for entry in class_grade_list if entry["ClassId"] == data['ClassId']), None)
                        if not any(d['ClassId'] == data['ClassId'] for d in class_grade_list):
                            # If not existing then append
                            class_grade_list.append({
                                'ClassId': data['ClassId'],
                                'DeansLister': data['DeansLister'],
                                'PresidentsLister': data['PresidentsLister'],
                                # Append Grade in array
                                'Grade': [data['StudentClassSubjectGrade']]
                            })
                            
                        else:
                            # If existing then append grade only
                            found_entry['Grade'].append(data['StudentClassSubjectGrade'])
                            
                    print('')
                    
                    for data in class_grade_list:
                        # print("ANALYTICS: ", data)
                        
                        # Check if grade is more than or equal to 1
                        if len(data['Grade']) >= 1:
                            # Get the sum of grade
                            sum_grade = sum(data['Grade'])
                            # Get the average grade rounded to 2 decimal places
                            average_grade = round(sum_grade / len(data['Grade']), 2)
                            # Update the Grade
                            data['Grade'] = average_grade
                            # Append average in course_grade_list
                            course_grade_list.append(average_grade)
                        else:
                            data['Grade'] = 0.00
                            
                        class_grade = db.session.query(ClassGrade).filter_by(ClassId = data['ClassId']).first()
                        
                        # print('DEANLISTER: ', data['DeansLister'])
                        # print('PRESIDENTSLISTER: ', data['PresidentsLister'])
                        # CLASS GRADE - Analytics for Class Grade Report
                        if class_grade:
                            # Update the class_grade
                            db.session.query(ClassGrade).filter_by(ClassId = data['ClassId']).update({
                                'DeansLister': data['DeansLister'],
                                'PresidentsLister': data['PresidentsLister'],
                                'Grade': data['Grade']
                            })             
                        else:
                            # Create a class_grade
                            new_class_grade = ClassGrade(
                                ClassId = data['ClassId'],
                                DeansLister = data['DeansLister'],
                                PresidentsLister = data['PresidentsLister'],
                                Grade = data['Grade']
                            )
                            
                            db.session.add(new_class_grade)
                            db.session.flush()

                        # Update the course grade by average of all class grade
                        # Check if course_grade is existing
                   
                    course_grade = db.session.query(CourseGrade).filter_by(CourseId = course_grade_data['CourseId'], Batch = course_grade_data['Batch'], Semester = course_grade_data['Semester']).first()
                    
                    average_course_grade = sum(course_grade_list) / len(course_grade_list)
                    
                    # COURSE GRADE - Calculating data of course grade
                    if course_grade:
                        # Update the course_grade
                        db.session.query(CourseGrade).filter_by(CourseId = course_grade_data['CourseId'], Batch = course_grade_data['Batch'], Semester = course_grade_data['Semester']).update({
                            'Grade': round(average_course_grade, 2)
                        })
                        
                        # # COURSE GRADE CHECKER
                        # print("\nUPDATED COURSE GRADE: " + str({
                        #     'CourseId': course_grade_data['CourseId'],
                        #     'Batch': course_grade_data['Batch'],
                        #     'Semester': course_grade_data['Semester'],
                        #     'Grade': round(average_course_grade, 2)
                        # }))
                    else:
                        # Create a course_grade
                        new_course_grade = CourseGrade(
                            CourseId = course_grade_data['CourseId'],
                            Batch = course_grade_data['Batch'],
                            Semester = course_grade_data['Semester'],
                            Grade = round(average_course_grade, 2)
                        )
                        
                        db.session.add(new_course_grade)
                        db.session.flush()
                        
                        # # COURSE GRADE CHECKER
                        # print("\nUPDATED COURSE GRADE: " + str({
                        #     'CourseId': course_grade_data['CourseId'],
                        #     'Batch': course_grade_data['Batch'],
                        #     'Semester': course_grade_data['Semester'],
                        #     'Grade': round(average_course_grade, 2)
                        # }))
                    
                    # COURSE ENROLLED - Checking if Student is already graduated (Status).
                    if student_list:
                        # for loop the student_list
                        for student_id in student_list:
                            # Get student id in "CourseEnrolled" column order by latest of "DateEnrolled"
                            course_enrolled = db.session.query(CourseEnrolled).filter_by(StudentId = student_id).order_by(desc(CourseEnrolled.DateEnrolled)).first()
                            # print('course_enrolled.DateEnrolled: ', course_enrolled.DateEnrolled)
                            
                            # Get the curriculum of course with the same batch
                            curriculum = db.session.query(Curriculum, Metadata, Subject).join(Metadata, Metadata.MetadataId == Curriculum.MetadataId).join(Subject, Subject.SubjectId == Curriculum.SubjectId).filter(Metadata.Batch == course_enrolled.DateEnrolled.year, Metadata.CourseId == course_grade_data['CourseId']).all()
                            
                            # For loop and print the Subject Name
                            bool_graduate = True;
                            for data in curriculum:
                                # print('data: ', data)
                                # Find class with the same StudentId
                                class_subject_grade_data = db.session.query(ClassSubject, StudentClassSubjectGrade).join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId).filter(StudentClassSubjectGrade.StudentId == student_id, ClassSubject.SubjectId == data.Subject.SubjectId).order_by(desc(StudentClassSubjectGrade.DateEnrolled)).first()
                                
                                # print('class_data: ', class_data)
                                
                                # Check if existing
                                if class_subject_grade_data:
                                    if class_subject_grade_data.StudentClassSubjectGrade.AcademicStatus == 1:
                                        # Go to next for loop of curriculum
                                        continue
                                    else:
                                        bool_graduate = False;
                                        
                                        # Set the CourseEnrolled Status to 0
                                        db.session.query(CourseEnrolled).filter_by(StudentId = student_id).update({
                                            'Status': 0
                                        })
                                        db.session.commit()
                                        break
                                else:
                                    bool_graduate = False;
                                    # Set the CourseEnrolled Status to 0
                                    db.session.query(CourseEnrolled).filter_by(StudentId = student_id).update({
                                        'Status': 0
                                    })
                                    db.session.commit()
                                    break     
                            # Check for value of flag if still true
                            if bool_graduate:
                                # Set the CourseEnrolled Status to 1
                                db.session.query(CourseEnrolled).filter_by(StudentId = student_id).update({
                                    'Status': 1
                                })
                                db.session.commit()
            else:   
                db.session.rollback()
                return jsonify({"error": "There no class yet"})
            print("SUCCESS")
            return jsonify({"success": True, "message": "Data finalized successfully"})
        else:
            return jsonify(None)
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))



def getClassListDropdown(batch=False):
    # Get all unique class with distinc of CourseId, Year, Section
    if batch:
        class_grade_query = db.session.query(Class, Metadata,  Course, ClassGrade).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(ClassGrade, ClassGrade.ClassId == Class.ClassId).all()
        
        if class_grade_query:
            # loop the data of it
            list_class = []
            for data in class_grade_query:
                section = str(data.Metadata.Year) + "-" + str(data.Class.Section)

                dict_class = {
                    "course": data.Course.CourseCode,
                    "section": section,
                    "batch": data.Metadata.Batch
                }
                # Append
                list_class.append(dict_class)
        
            return list_class
    else:
        class_grade_query = db.session.query(Class, Metadata,  Course, ClassGrade).join(Metadata, Metadata.MetadataId == Class.MetadataId).join(Course, Course.CourseId == Metadata.CourseId).join(ClassGrade, ClassGrade.ClassId == Class.ClassId).distinct(Course.CourseId, Metadata.Year, Class.Section).all()
        
        if class_grade_query:
            # loop the data of it
            list_class = []
            for data in class_grade_query:
                section = str(data.Metadata.Year) + "-" + str(data.Class.Section)

                dict_class = {
                    "course": data.Course.CourseCode,
                    "section": section
                }
                # Append
                list_class.append(dict_class)
        
            return list_class


def getStatistics():
    try:
        # Get the teacher active in Faculty
        teacher_active_count = db.session.query(Faculty).filter_by(is_active = True).count()
        
        
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




def getListersCount():
    try:
        
        def get_classes_query(current_year):
            return (
                db.session.query(
                    Metadata.CourseId,
                    Course.CourseCode,
                    func.sum(ClassGrade.DeansLister).label('deans_lister_count'),
                    func.sum(ClassGrade.PresidentsLister).label('presidents_lister_count')
                )
                .join(Class, Metadata.MetadataId == Class.MetadataId)
                .join(Course, Course.CourseId == Metadata.CourseId)
                .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                .filter(Metadata.Batch == current_year)
                .group_by(Metadata.CourseId, Course.CourseCode)
                .all()
            )
            
        current_year = datetime.now().year
        print('current_year:', current_year)

        # Get classes query for the current year
        classes_query = get_classes_query(current_year)

        # If there are no results, try the previous year
        if not classes_query:
            current_year -= 1
            classes_query = get_classes_query(current_year)

        list_lister_data = []

        for result in classes_query:
            course_id, course_code, deans_lister_count, presidents_lister_count = result
            print(f"Course ID: {course_id}, Course Code: {course_code}, Deans Lister Count: {deans_lister_count}, Presidents Lister Count: {presidents_lister_count}")

            # Make a dictionary for it
            dict_lister_data = {
                'CourseId': course_id,
                'CourseCode': course_code,
                'DeansListerCount': deans_lister_count,
                'PresidentsListerCount': presidents_lister_count
            }
            # Append
            list_lister_data.append(dict_lister_data)

        # Return all elements
        return jsonify({'success': True, 'result': list_lister_data})
    except Exception as e:
        # Rollback the changes in case of an error
        db.session.rollback()
        # Return an error response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
