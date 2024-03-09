from models import StudentClassGrade, ClassGrade, Class, Course, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, db, UniversityAdmin, ClassSubjectGrade, Metadata, Curriculum, LatestBatchSemester, SystemAdmin, OAuth2Client

from sqlalchemy import desc, distinct, func, and_

import re
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict
from datetime import date, datetime

from flask import session, jsonify
from static.js.utils import convertGradeToPercentage, checkStatus
import pandas as pd
from collections import defaultdict

def getCurrentUser():
    current_user_id = session.get('user_id')
    return SystemAdmin.query.get(current_user_id)

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


def updateSystemAdminData(str_univ_admin_id, number, residentialAddress):
    try:
        if not re.match(r'^09\d{9}$', number):
            return {"type": "mobile", "status": 400}

        if residentialAddress is None or residentialAddress.strip() == "":
            return {"type": "residential", "status": 400}

        # Update the student data in the database
        data_systemAdmin = db.session.query(SystemAdmin).filter(
            SystemAdmin.SysAdminId == str_univ_admin_id).first()
        
        if data_systemAdmin:
            data_systemAdmin.MobileNumber = number
            data_systemAdmin.ResidentialAddress = residentialAddress
            db.session.commit()
                        
            return {"message": "Data updated successfully", "number": number, "residentialAddress": residentialAddress, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}


def updatePassword(str_system_admin_id, password, new_password, confirm_password):
    try:
        data_system_admin = db.session.query(SystemAdmin).filter(SystemAdmin.SysAdminId == str_system_admin_id).first()

  
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
            
        
        if data_system_admin:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_system_admin.Password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(new_password)
                data_system_admin.Password = new_hashed_password
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
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None


def getClientList(skip, top, order_by, filter):
    try:
        clients = OAuth2Client.query.all()
        total_count = OAuth2Client.query.count()
        list_client = []
        for client in clients:
            list_client.append({"Id": client.id, "ClientName": client.client_metadata['client_name'], 'ClientId': client.client_id, 'ClientURI': client.client_metadata['client_uri']})
            
        if clients:
            return jsonify({ 'result': list_client, 'count': total_count})
        else:
            return jsonify({"result": [], 'count': 0})
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}
    
    
def getClientsData(Id):
    try:
        clients = db.session.query(OAuth2Client).filter_by(id = Id).first()
        
        if clients:
            dict_clients = {
                "ClientName": clients.client_metadata['client_name'], 
                "ClientId": clients.client_id, 
                "ClientURI": clients.client_metadata['client_uri'],
                "ClientSecret": clients.client_secret,
                "Scope": clients.client_metadata['scope'],
                "GrantType": clients.client_metadata['grant_types']
            }
            return jsonify({ 'result': dict_clients, 'success': True})
        else:
            return jsonify({"message": "No clients found"}), 404
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}
    
    
    
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
        
        total_count = order_query.count()
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
            return {'result': list_classes, 'count': total_count}
        else:
            return None

    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None



 
def getBatchSemester(skip, top, order_by, filter):
    try:
        
        batch_semester_query = db.session.query(LatestBatchSemester)
        
        # Order default
        # .order_by(desc(Metadata.Batch), desc(Metadata.Semester))


        filter_conditions = []
        if filter:
            filter_parts = filter.split(' and ')
            for part in filter_parts:
                # Check if part has to lower in value
                if '(tolower(' in part:
                    print("STRING FUNCTIONS")
                    # # Extracting column name and value
                    # column_name = part.split("(")[3].split("),'")[0]
                    # value = part.split("'")[1]
                    # column_str = None
                    
                    # if column_name.strip() == 'CourseCode':
                    #     column_str = getattr(Course, 'CourseCode')
                    # elif column_name.strip() == 'Course':
                    #     column_str = getattr(Course, 'Name')
                 
                    # if column_str:
                    #     # Append column_str
                    #     filter_conditions.append(
                    #         func.lower(column_str).like(f'%{value}%')
                    #     )
                else:
                    # column_name = part[0][1:]  # Remove the opening '('
                    column_name, value = [x.strip() for x in part[:-1].split("eq")]
                    column_name = column_name[1:]
                    column_num = None
                    int_value = value.strip(')')
                    
                    # Check for column name 
                    if column_name.strip() == 'Batch':
                        column_num = LatestBatchSemester.Batch
                    elif column_name.strip() == 'Semester':
                        column_num = LatestBatchSemester.Semester
    
                    
                    if column_num:
                        # Append column_num
                        filter_conditions.append(
                            column_num == int_value
                        )
                # END OF ELSE PART
            # END OF FOR LOOP
                
        
        # Apply all filter conditions with 'and'
  
        filter_query = batch_semester_query.filter(and_(*filter_conditions))
        
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(LatestBatchSemester, 'Batch')
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(LatestBatchSemester, 'Semester')           
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(LatestBatchSemester.Batch), desc(LatestBatchSemester.Semester))
            # order params
            

        latest_batch_semester_main_query = order_query.offset(skip).limit(top).all()
        total_count = order_query.count()

        list_metadata = []
        if latest_batch_semester_main_query:
            for data in latest_batch_semester_main_query:
                # Create a dict
                # Get the data to dict
                dict_metadata = data.to_dict()

                # Append the dict to the list_metadata
                list_metadata.append(dict_metadata)
            
            return jsonify({'result': list_metadata, 'count': total_count})
        else:
            return jsonify({'result': None})
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return jsonify(error=str(e))



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
            print("ELSE")
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
                    "LastName": data.Student.LastName,
                    "FirstName": data.Student.FirstName,
                    "MiddleName": data.Student.MiddleName,
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
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None




def getFacultyData(skip, top, order_by, filter):
    try:
        faculty_query = (
            db.session.query(Faculty)
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
                        column_str = getattr(Faculty, 'StudentNumber')
                    elif column_name.strip() == 'LastName':
                        column_str = getattr(Faculty, 'LastName')
                    elif column_name.strip() == 'FirstName':
                        column_str = getattr(Faculty, 'FirstName')
                    elif column_name.strip() == 'MiddleName':
                        column_str = getattr(Faculty, 'MiddleName')
                    elif column_name.strip() == 'Email':
                        column_str =  getattr(Faculty, 'Email')     
                    elif column_name.strip() == 'MobileNumber':
                        column_str = getattr(Faculty, 'MobileNumber')
                    elif column_name.strip() == 'CourseCode':
                        column_str = getattr(Faculty, 'CourseCode')
                    elif column_name.strip() == 'DateEnrolled':
                        column_str = getattr(Faculty, 'DateEnrolled')
                        filter_conditions.append(
                            CourseEnrolled.DateEnrolled == (1 if value == 'male' else 2)
                        )
                    elif column_name.strip() == 'Gender':
                        filter_conditions.append(
                            Faculty.Gender == (1 if value == 'male' else 2)
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
                        
        filter_query = faculty_query.filter(and_(*filter_conditions))
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Faculty, 'StudentNumber')
            elif order_by.split(' ')[0] == "LastName":
                order_attr = getattr(Faculty, 'LastName')
            elif order_by.split(' ')[0] == "FirstName":
                order_attr = getattr(Faculty, 'FirstName')
            elif order_by.split(' ')[0] == "MiddleName":
                order_attr = getattr(Faculty, 'MiddleName')
            elif order_by.split(' ')[0] == 'Email':
                order_attr = getattr(Faculty, 'Email')
            elif order_by.split(' ')[0] == 'Gender':
                order_attr = getattr(Faculty, 'Gender')
            elif order_by.split(' ')[0] == 'MobileNumber':
                order_attr = getattr(Faculty, 'MobileNumber')
            elif order_by.split(' ')[0] == 'CourseCode':
                order_attr = getattr(Faculty, 'CourseCode')
            elif order_by.split(' ')[0] == 'DateEnrolled':
                order_attr = getattr(Faculty, 'DateEnrolled')
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(Faculty, 'CurriculumYear')
           
           
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(desc(Faculty.Status))
        
        
        # Query for counting all records
        total_count = order_query.count()
        # Limitized query = 
        student_limit_offset_query = order_query.offset(skip).limit(top).all()
        if student_limit_offset_query:
             # For loop the student_query and put it in dictionary
            list_student_data = []
            for data in student_limit_offset_query:
                dict_student = {
                    "FacultyId": data.FacultyId,
                    "FacultyCode": data.FacultyCode,
                    "LastName": data.LastName,
                    "FirstName": data.FirstName,
                    "MiddleName": data.MiddleName if data.MiddleName else "",
                    "Email": data.Email,
                    "MobileNumber": data.MobileNumber,
                    "Gender": "Male" if data.Gender == 1 else "Female",
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


def updateStudentData(studentId, updated_data):
    try:
        # Get LastName, FirstName, MiddleName, MobileNumber, DateEnrolled, Email
        # Check if studentId exists
        student = (
            db.session.query(CourseEnrolled, Student, Course).join(Student, Student.StudentId == CourseEnrolled.StudentId).join(Course, Course.CourseId == CourseEnrolled.CourseId).filter(Student.StudentId == studentId).first()
        )
        if student:
            # Update student using student.update of LastName
            student.Student.LastName = updated_data['LastName']
            db.session.commit()
            
            return updated_data
  
            # return jsonify({ "message": "Data updated successfully", "status": 200})
        else:
            db.session.rollback()
            return jsonify({"message": "Something went wrong", "status": 404})
       
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}
    
    

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
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e})
    

def revertFinalizedGrades(latestBatchSemesterId):
    try:
        # Get latest Batch semester
        latest_batch_semester = db.session.query(LatestBatchSemester).filter_by(LatestBatchSemesterId = latestBatchSemesterId).first()
        print('latest_batch_semester: ', latest_batch_semester)
        if latest_batch_semester:
            # Make the IsGradeFinalized False
            latest_batch_semester.IsGradeFinalized = False
            # Get all class in it
            classes = db.session.query(Class, Metadata).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Metadata.Batch == latest_batch_semester.Batch, Metadata.Semester == latest_batch_semester.Semester).all()
            
            if classes:
                # Loop and change the value of Class.IsGradeFinalized to False
                for cls in classes:
                    cls.Class.IsGradeFinalized = False
                    db.session.commit()
            # rollbacck
            db.session.rollback()
            return jsonify({"success": True, "message": "Successfully reverted the grades"})
        
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e})
    

def updateGradesStudent(updated_data):
    try:
        
        print('updated_data: ', updated_data)
        return jsonify({"success": True, "message": "Successfully reverted the grades"}), 400
        
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e})
    


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
                    elif column_name.strip() == 'LastName':
                        column_str = getattr(Student, 'LastName')
                    elif column_name.strip() == 'FirstName':
                        column_str = getattr(Student, 'FirstName')
                    elif column_name.strip() == 'MiddleName':
                        column_str = getattr(Student, 'MiddleName')
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
                    elif column_name.strip() == 'Remarks':
                        column_num = StudentClassSubjectGrade.AcademicStatus
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
            elif order_by.split(' ')[0] == "LastName":
                order_attr = getattr(Student, 'LastName')
            elif order_by.split(' ')[0] == "FirstName":
                order_attr = getattr(Student, 'FirstName')
            elif order_by.split(' ')[0] == "MiddleName":
                order_attr = getattr(Student, 'MiddleName')
            elif order_by.split(' ')[0] == 'Grade':
                order_attr = getattr(StudentClassSubjectGrade, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'SubjectCode':
                order_attr = getattr(Subject, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            elif order_by.split(' ')[0] == 'Semester':
                order_attr = getattr(Metadata, order_by.split(' ')[0])
            else:

                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(Course.CourseCode), desc(Metadata.Year), desc(Class.Section))
                
                else:
                    order_query = filter_query.order_by(Course.CourseCode, Metadata.Year, Class.Section)
                # close the if_order by and go to next line of it

            # Check if order_by contains space
            if not order_by.split(' ')[0] == "Class":
                if ' ' in order_by:
                    order_query = filter_query.order_by(desc(order_attr))
                else:
                    order_query = filter_query.order_by(order_attr)
        else:
            # Apply default sorting
            order_query = filter_query.order_by(
                desc(Course.CourseCode), desc(Metadata.Batch), desc(Metadata.Year), desc(Metadata.Semester), Student.LastName
            )

        # Check if order_query and filter query exists:
        total_count = order_query.count()
        result_all = order_query.offset(skip).limit(top).all()
       
        if result_all:
            list_data_class_subject_grade = []
            unique_classes = set()
     
            for class_subject_grade in result_all:
                remarks = ""
                class_name = f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Metadata.Year}-{class_subject_grade.Class.Section}"
                if class_subject_grade.StudentClassSubjectGrade.AcademicStatus == 1:
                    remarks = "Passed"
                elif class_subject_grade.StudentClassSubjectGrade.AcademicStatus == 2:
                    remarks = "Failed"
                elif class_subject_grade.StudentClassSubjectGrade.AcademicStatus == 3:
                    remarks = "Incomplete"
                else:
                    remarks = "Withdrawn"

                dict_class_subject_grade = {
                    'ClassSubjectId': class_subject_grade.ClassSubject.ClassSubjectId ,
                    'StudentId': class_subject_grade.Student.StudentId,
                    'StudentNumber': class_subject_grade.Student.StudentNumber,
                    'LastName': class_subject_grade.Student.LastName,
                    'FirstName': class_subject_grade.Student.FirstName,
                    'MiddleName': class_subject_grade.Student.MiddleName,
                    'Class': class_name,
                    'Batch': class_subject_grade.Metadata.Batch,
                    'Semester': class_subject_grade.Metadata.Semester,
                    'Grade': class_subject_grade.StudentClassSubjectGrade.Grade,
                    'SubjectCode': class_subject_grade.Subject.SubjectCode,
                    'Remarks': remarks
                }

                list_data_class_subject_grade.append(dict_class_subject_grade)
                unique_classes.add(class_name)

            sorted_unique_classes = sorted(unique_classes)
      
            # Return the list of class grades, the classes, and pagination information
            return jsonify({'result':list_data_class_subject_grade, 'count': total_count, 'classes': list(sorted_unique_classes)})
        else:
            return {'ClassSubjectGrade': [], 'Classes': [], 'currentPage': 1, 'totalPages': 0, 'totalItems': 0}

    except Exception as e:
        print("ERROR: ", e)
        # Log the exception or handle it appropriately
        return None
    



def processGradeResubmission(file):
    try:
        # Check if the file is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please select an Excel file.'}), 400

        # Read the Excel file into a DataFrame
        df = pd.read_excel(file)
        
        list_error = []
        is_some_submitted = False
        # Now you can access and manipulate the data in the DataFrame
        # For example, you can iterate through rows and access columns like this:
        for index, row in df.iterrows():
            # Extract the values from the DataFrame
            student_number = row['Student Number'] # OK
            student_lastname = row['LastName']
            student_firstname = row['FirstName']
            student_middlename = row['MiddleName']
            section_code = row['Section Code']
            subject_code = row['SubjectCode'] # OK
            semester = row['Semester'] # OK
            grade = row['Grade']
            batch = row['Batch'] # OK
            
            # print full name
            print(f"{student_lastname}, {student_firstname} {student_middlename}")
            # Split the section_code by the last space and keep the first part
            course_code = section_code.rsplit(' ', 1)[0] 
            
            # Split the section_code by space, get the last part, and split it by hyphen '-' to extract year and section
            year, section = section_code.split(' ')[-1].split('-')
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
                .order_by(desc(Student.LastName), desc(Metadata.Year), desc(Class.Section), desc(Metadata.Batch))
                .first()
            )
            
            if student_data:
                # check if AcademicStatus student_data.StudentClassSubjectGrade is 3
                if student_data.StudentClassSubjectGrade.AcademicStatus == 3:
                    
                    class_subject_grade = (
                        db.session.query(ClassSubjectGrade)
                        .filter(ClassSubjectGrade.ClassSubjectId == student_data.ClassSubject.ClassSubjectId)
                        .first()
                    )
                    
                    student_class_grade = (
                        db.session.query(StudentClassGrade)
                        .filter(StudentClassGrade.ClassId == student_data.Class.ClassId, StudentClassGrade.StudentId == student_data.Student.StudentId)
                        .first()
                    )
                    
                    class_grade = (
                        db.session.query(ClassGrade)
                        .filter(ClassGrade.ClassId == student_data.Class.ClassId)
                        .first()
                    )
                    
                    # Update the grade STUDENT CLASS SUBJECT GRADE UPDATE
                    student_data.StudentClassSubjectGrade.Grade = grade
                    student_data.StudentClassSubjectGrade.AcademicStatus = 1
                    db.session.add(student_data.StudentClassSubjectGrade)
                    # STUDENT CLASS GRADE UPDATE
                    # Get student class grade
                    
                    student_class_average_grade = db.session.query(func.avg(StudentClassSubjectGrade.Grade)).\
                        join(ClassSubject, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId).\
                        join(Class, Class.ClassId == ClassSubject.ClassId).\
                        filter(Class.ClassId == student_data.Class.ClassId, 
                            StudentClassSubjectGrade.StudentId == student_data.Student.StudentId).\
                        group_by(Class.ClassId).\
                        scalar()

                    print('student_class_grade.Grade: ', student_class_grade.Grade)
                    # If student_class_grade is an instance of your ORM model, update its Grade attribute with the calculated average grade
                    student_class_grade.Grade = round(float(student_class_average_grade), 2)
                    db.session.add(student_class_grade)
                    
                                        
                    print("HERE CHECKER")
                    # Get average grade for StudentClassSUbjectGrade with the same ClassSubjectId
                    class_subject_average_grade = db.session.query(func.avg(StudentClassSubjectGrade.Grade)).\
                        join(ClassSubject, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId).\
                        join(Class, Class.ClassId == ClassSubject.ClassId).\
                        filter(Class.ClassId == student_data.Class.ClassId).\
                        group_by(Class.ClassId).\
                        scalar()
                    
                    class_subject_grade.Grade == round(float(class_subject_average_grade), 2)  
                    class_subject_grade.Passed += 1
                    class_subject_grade.Incomplete -= 1
                    db.session.add(class_subject_grade)
                    
                    
                    print('class_subject_average_grade: ', round(float(class_subject_average_grade), 2))
                    
                    # Get class grade through average of StudentClassGrade that has the same ClassId
                    class_average_grade = db.session.query(func.avg(StudentClassGrade.Grade)).\
                        join(Class, Class.ClassId == StudentClassGrade.ClassId).\
                        filter(Class.ClassId == student_data.Class.ClassId, StudentClassGrade.Grade != 0).\
                        group_by(Class.ClassId).\
                        scalar()
                    print('class_average_grade: ', round(float(class_average_grade), 2))
                    class_grade.Grade = round(float(class_average_grade), 2) 
                    db.session.add(class_grade)
                    is_some_submitted = True
                    db.session.commit()
                else:
                    db.session.rollback()
                    list_error.append({
                        "StudentNumber": student_number,
                        "LastName": student_lastname,
                        "FirstName": student_firstname,
                        "MiddleName": student_middlename,
                        "SectionCode": section_code,
                        "SubjectCode": subject_code,
                        "Semester": semester,
                        "Grade": grade,
                        "Batch": batch,
                        "Error": "You cannot modify grade for this student"
                    })
                    
        if list_error and is_some_submitted:
            return jsonify({'warning': 'Some data cannot be updated', 'errors': list_error}), 400
        elif list_error and not is_some_submitted:
            return jsonify({'error': 'All data cannot be modified', 'errors': list_error}), 400
        else:
            return jsonify({'result': 'File uploaded and data processed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        print("ERROR: ", e)
        return jsonify({'error': 'An error occurred while processing the file'}), 500
    