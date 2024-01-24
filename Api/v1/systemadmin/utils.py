from models import StudentClassGrade, ClassGrade, Class, Course, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, db, UniversityAdmin, ClassSubjectGrade, Metadata, Curriculum, LatestBatchSemester, SystemAdmin, OAuth2Client

from sqlalchemy import desc, distinct, func, and_

import re
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict
from datetime import date, datetime

from flask import session, jsonify
from static.js.utils import convertGradeToPercentage, checkStatus

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
            return jsonify({"message": "No clients found"}), 404
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
            order_query = filter_query.order_by(desc(Faculty.IsActive))
        
        
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
                    "MiddleName": data.MiddleName,
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
            # db.session.commit()
            # rollbacck
            db.session.rollback()
            return jsonify({"success": True, "message": "Successfully reverted the grades"})
        
    except Exception as e:
        print("ERROR: ", e)
        db.session.rollback()
        # Handle the exception here, e.g., log it or return an error response
        return jsonify({'error': e})