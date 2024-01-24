from models import StudentClassGrade, Class, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, Course, ClassGrade, ClassSubjectGrade, Metadata, db, LatestBatchSemester

from sqlalchemy import desc, distinct, func, and_
import re
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from flask import session,  jsonify
import pandas as pd

from static.js.utils import convertGradeToPercentage, checkStatus

def getCurrentUser():
    current_user_id = session.get('user_id')
    return Faculty.query.get(current_user_id)


def getAllClassAverageWithPreviousYear(str_teacher_id):
    try:
        #  # Get LatestBatchSemester.IsGradeFinalized == True
        # latest_batch_semester = db.session.query(LatestBatchSemester).filter(LatestBatchSemester.IsGradeFinalized == False, LatestBatchSemester.IsEnrollmentStarted == True).order_by(desc(LatestBatchSemester.created_at)).first()
        
        # print('latest_batch_semester: ', latest_batch_semester.Batch)
        
        # # current_year = datetime.datetime.now().year

        # data_class_subject_grade_handle = (
        #     db.session.query(
        #         ClassSubject,
        #         Class, Course, Metadata
        #     )
        #     .join(Class, Class.ClassId == ClassSubject.ClassId)
        #     .join(Metadata, Metadata.MetadataId == Class.MetadataId)
        #     .join(Course, Course.CourseId == Metadata.CourseId)
        #     .filter(ClassSubject.FacultyId == str_teacher_id, Metadata.Batch == latest_batch_semester.Batch)
        #     .order_by(desc(Metadata.CourseId), Metadata.Year, Class.Section)
        #     .all()
        # )

        # if data_class_subject_grade_handle:
        #     list_classes = []
        #     seen_class_name = set()  # Initialize a set to track seen ClassIds

        #     for class_subject_grade in data_class_subject_grade_handle:
        #         class_name = f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Metadata.Year}-{class_subject_grade.Class.Section}"

        #         # Check if the ClassId is not in the seen_class_name set
        #         if class_name not in seen_class_name:
        #             # Get the class name
        #             class_obj = {
        #                 'ClassId': class_subject_grade.Class.ClassId,
        #                 'ClassName': class_name
        #             }

        #             # Add class_name to the seen_class_name set
        #             seen_class_name.add(class_name)

        #             # Add class_obj to the list_classes
        #             list_classes.append(class_obj)

        #     # Return the list of class objects
        #     return {'Classes': list_classes}
# data_class_grade_handle = (
#             db.session.query(
#                 ClassSubject,
#                 Class,
#                 Metadata,
#                 ClassGrade,
#                 Course,
#             )
#             .join(Class, ClassSubject.ClassId == Class.ClassId)
#             .join(Metadata, Metadata.MetadataId == Class.MetadataId)
#             .join(ClassGrade, Class.ClassId == ClassGrade.ClassId)
#             .join(Course, Metadata.CourseId == Course.CourseId)
#             .filter(ClassSubject.FacultyId == str_teacher_id, Metadata.Batch == latest_batch_semester.Batch)
#             .distinct(Metadata.CourseId, Metadata.Year, Metadata.Batch)
#             .order_by(desc(Metadata.Year)).all()
#             # I Limit this into 8 because teacher cannot have many classes and the data sets made are distributed almost all of them
            
#             # Once the data sets is fixed this can replace the previous line
#             # .all()
#         )
        
        # Get LatestBatchSemester.IsGradeFinalized == True
        latest_batch_semester = db.session.query(LatestBatchSemester).filter(LatestBatchSemester.IsGradeFinalized == False, LatestBatchSemester.IsEnrollmentStarted == True).order_by(desc(LatestBatchSemester.created_at)).first()
        
        print('latest_batch_semester: ', latest_batch_semester.Batch)
        
       # Get all class subjects taught by a specific faculty member in the latest batch and semester
        data_class_subject_grade_handle = db.session.query( ClassSubject.FacultyId, Class.ClassId, Metadata.Batch, Metadata.CourseId, Course.CourseCode, Metadata.Year, Class.Section, func.count(ClassSubject.ClassSubjectId).label('CountClassSubject'), ) .join(Class, Class.ClassId == ClassSubject.ClassId) .join(Metadata, Metadata.MetadataId == Class.MetadataId) .join(Course, Metadata.CourseId == Course.CourseId) .filter( ClassSubject.FacultyId == str_teacher_id, Metadata.Batch == latest_batch_semester.Batch, Class.IsGradeFinalized == False ) .group_by( ClassSubject.FacultyId, Class.ClassId, Metadata.Batch, Metadata.CourseId, Course.CourseCode, Metadata.Year, Class.Section, ) .all()

        print('data_class_subject_grade_handle: ', data_class_subject_grade_handle)
        if data_class_subject_grade_handle:
            list_data_class_grade = []
            for data in data_class_subject_grade_handle:
                

                class_batch = data[2]
                class_section = data[6]
                class_year = data[5]
                course_code = data[4]
                
                class_name = f"{course_code} {class_year}-{class_section} ({class_batch})"

                dict_class_grade_handle = {
                    'Class': class_name,
                    'AYear': class_year,
                    'BSection': class_section,
                    'Batch': class_batch,
                    'ListGrade': []
                }

                list_grade = []
                print('class_name: ', class_name)
                for i in range(1, class_year+1):

                    batch = class_batch - class_year + i

                    class_grade_result = (
                        db.session.query(
                            Class.ClassId,
                            Metadata.Batch,
                            (func.avg(func.nullif(ClassGrade.Grade, 0))).label("Avg"),
                        )
                        .join(Metadata, Metadata.MetadataId == Class.MetadataId)
                        .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                        .filter(Metadata.Year == i, Metadata.Batch == batch, Class.Section == class_section)
                        .group_by(Class.ClassId, Metadata.Batch)
                        # I Limit this into 8 because teacher cannot have many classes and the data sets made are distributed almost all of them
                        .first()
                        # Once the data sets is fixed this can replace the previous line
                        # .all()
                    )
                    print('class_grade_result.ClassGrade.Grade: ', class_grade_result[0])
                    print('class_grade_result.ClassGrade.COUNT: ', class_grade_result[1])
                    list_grade.append(
                        {'x': class_grade_result[1], 'y': convertGradeToPercentage(class_grade_result[2])})
                dict_class_grade_handle['ListGrade'].extend(list_grade)

                list_data_class_grade.append(dict_class_grade_handle)

            # Return the list of class grades and the lowest/highest grades dictionary
            return (list_data_class_grade)
        else:
            return None
                # dict_class_grade_handle['ListGrade'].extend(list_grade)

                # list_data_class_grade.append(dict_class_grade_handle)

            # Return the list of class grades and the lowest/highest grades dictionary
            # return (list_data_class_grade)
        

        # print('str_teacher_id: ', str_teacher_id)
        # if data_class_grade_handle:
        #     list_data_class_grade = []

        #     for class_grade_handle in data_class_grade_handle:
        #         # Calculate class name
        #         class_name = f"{class_grade_handle.Course.CourseCode} {class_grade_handle.Metadata.Year}-{class_grade_handle.Class.Section} ({class_grade_handle.Metadata.Batch})"

        #         num_class_batch = class_grade_handle.Metadata.Batch
        #         num_class_section = class_grade_handle.Class.Section

        #         dict_class_grade_handle = {
        #             'Class': class_name,
        #             'AYear': class_grade_handle.Metadata.Year,
        #             'BSection': num_class_section,
        #             'Batch': num_class_batch,
        #             'ListGrade': []
        #         }

        #         list_grade = []
        #         # 2022 - 4-i = 3 = 2019 1st Year
        #         #       4-2 = 2 = 2020 2nd Year
        #         # 4th year 2022 -
        #         # 3rd year 2021
        #         # 2nd year 2020
        #         # 1st year 2019
        #         for i in range(1, class_grade_handle.Metadata.Year+1):

        #             batch = class_grade_handle.Metadata.Batch - class_grade_handle.Metadata.Year + i

        #             class_grade_result = (
        #                 db.session.query(
        #                     Class,
        #                     Metadata,
        #                     ClassGrade,
        #                 )
        #                 .join(Metadata, Metadata.MetadataId == Class.MetadataId)
        #                 .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
        #                 .filter(Metadata.Year == i, Metadata.Batch == batch, Class.Section == num_class_section)
        #                 # I Limit this into 8 because teacher cannot have many classes and the data sets made are distributed almost all of them
        #                 .first()
        #                 # Once the data sets is fixed this can replace the previous line
        #                 # .all()
        #             )

        #             list_grade.append(
        #                 {'x': class_grade_result.Metadata.Batch, 'y': convertGradeToPercentage(class_grade_result.ClassGrade.Grade)})

        #         dict_class_grade_handle['ListGrade'].extend(list_grade)

        #         list_data_class_grade.append(dict_class_grade_handle)

            # Return the list of class grades and the lowest/highest grades dictionary
            # return (list_data_class_grade)
        # else:
        #     return None

    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None


def getHighLowAverageClass(str_teacher_id):

    try:
        current_year = datetime.datetime.now().year
        print('CURRENY YEEARL:  ', current_year)
        data_lowest_grade_class_handle = (
            db.session.query(
                ClassSubject,
                Class,
                Metadata,
                ClassGrade,
                Course,
            )
            .join(Class, ClassSubject.ClassId == Class.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(ClassGrade, Class.ClassId == ClassGrade.ClassId)
            .join(Course, Metadata.CourseId == Course.CourseId)
            .filter(ClassSubject.FacultyId == str_teacher_id, Class.IsGradeFinalized == True)
            .order_by(ClassGrade.Grade.desc())
            .first()
        )
        print('data_lowest_grade_class_handle: ', data_lowest_grade_class_handle)
        data_highest_grade_class_handle = (
            db.session.query(
                ClassSubject,
                Class,
                Metadata,
                ClassGrade,
                Course,
            )
            .join(Class, ClassSubject.ClassId == Class.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(ClassGrade, Class.ClassId == ClassGrade.ClassId)
            .join(Course, Metadata.CourseId == Course.CourseId)
            .filter(ClassSubject.FacultyId == str_teacher_id, Class.IsGradeFinalized == True)
            .order_by(ClassGrade.Grade)
            .first()
        )

        highest_grade = round(data_highest_grade_class_handle.ClassGrade.Grade, 2)
        lowest_grade = round(data_lowest_grade_class_handle.ClassGrade.Grade, 2)

        highest_class = f"{data_highest_grade_class_handle.Course.CourseCode} {data_highest_grade_class_handle.Metadata.Year}-{data_highest_grade_class_handle.Class.Section} ({data_highest_grade_class_handle.Metadata.Batch})"
        lowest_class = f"{data_lowest_grade_class_handle.Course.CourseCode} {data_lowest_grade_class_handle.Metadata.Year}-{data_lowest_grade_class_handle.Class.Section} ({data_lowest_grade_class_handle.Metadata.Batch})"

        # Return the list of class grades and the lowest/highest grades dictionary
        return {
            "highest": highest_grade,
            "highestClass": highest_class,
            "lowest": lowest_grade,
            "lowestClass": lowest_class
        }

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getSubjectCount(str_teacher_id):
    try:
        # Get Latest Batch Semester where IsGradeFinalized is False and IsEnrollmentStarted to True
        latest_batch_semester = db.session.query(LatestBatchSemester).filter(LatestBatchSemester.IsGradeFinalized == False, LatestBatchSemester.IsEnrollmentStarted == True).order_by(desc(LatestBatchSemester.created_at)).first()
        
        data_subject_amount = (
            db.session.query(
                func.count(distinct(ClassSubject.SubjectId))
            )
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .filter(ClassSubject.FacultyId == str_teacher_id, Metadata.Batch == latest_batch_semester.Batch, Metadata.Semester == latest_batch_semester.Semester)
            .scalar()
        )

        return {"subjectCount": data_subject_amount}
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getPassFailRates(str_teacher_id):
    try:

        data_pass_fail_rates = (
            db.session.query(
                ClassSubject,
                ClassSubjectGrade,
                Class,
                Metadata,
                Subject
            )
            .join(ClassSubjectGrade, ClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
            .filter(ClassSubject.FacultyId == str_teacher_id)
            .distinct(Metadata.CourseId, Metadata.Year, Metadata.Batch)
            .order_by(desc(Metadata.Batch))
            .all()
        )

        if data_pass_fail_rates:
            list_pass_fail_rates = []

            for pass_fail_rates in data_pass_fail_rates:
                dict_pass_fail_rate = {
                    'Year': pass_fail_rates.Metadata.Batch,
                    'Passed': pass_fail_rates.ClassSubjectGrade.Passed,
                    'Failed': pass_fail_rates.ClassSubjectGrade.Failed,
                    'Dropout': pass_fail_rates.ClassSubjectGrade.Dropout,
                }
                list_pass_fail_rates.append(dict_pass_fail_rate)

            aggregated_data = {}

            for entry in list_pass_fail_rates:
                year = entry['Year']
                passed = entry['Passed']
                failed = entry['Failed']
                dropout = entry['Dropout']

                if year in aggregated_data:
                    aggregated_data[year]['Passed'] += passed
                    aggregated_data[year]['Failed'] += failed
                    aggregated_data[year]['Dropout'] += dropout
                else:
                    aggregated_data[year] = {
                        'Year': year,
                        'Passed': passed,
                        'Failed': failed,
                        'Dropout': dropout
                    }

            return list(aggregated_data.values())

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getTopPerformerStudent(skip, top, order_by, filter):
    try:

        data_top_performer_student = (
            db.session.query(
                Student.StudentId,
                Student.StudentNumber,
                Student.LastName,
                Student.FirstName,
                Student.MiddleName,
                Metadata.Batch,
                func.avg(StudentClassGrade.Grade).label('average_grade'),
            )
            .join(Student, Student.StudentId == StudentClassGrade.StudentId)
            .join(Class, Class.ClassId == StudentClassGrade.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
           
            # .group_by(Student.StudentId, Metadata.Batch)
            # .limit(10)
            # .all()
        )
        
        # DEWFAULT:
        #  .filter(Class.IsGradeFinalized == True)
        #  .order_by(desc(Metadata.Batch), ('average_grade'))  # Order by average_grade in descending order
        
        print('data_top_performer_student: ', data_top_performer_student)
        
        filter_conditions = []
        
        filter_conditions.append(
            Class.IsGradeFinalized == True
        )
        
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
                    elif column_name.strip() == 'Grade':
                        filter_conditions.append(
                            ClassGrade.Grade == value
                        )
                        continue
                    # elif column_name.strip() == 'Batch':
                    #     filter_conditions.append(
                    #         Metadata.Batch == value
                    #     )
                    #     continue
                 
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
        else:
            print("NO FILTER")
        
        # Apply all filter conditions with 'and'
  
        filter_query = data_top_performer_student.filter(and_(*filter_conditions))
        # print('FILTER: ', filter_query.statement.compile().params)
        
        
         # Apply sorting logic
        if order_by:
            # Determine the order attribute
            if order_by.split(' ')[0] == 'StudentNumber':
                order_attr = getattr(Student, 'StudentNumber')
            elif order_by.split(' ')[0] == "LastName":
                order_attr = getattr(Student, "LastName")
            elif order_by.split(' ')[0] == 'FirstName':
                order_attr = getattr(Student, 'FirstName')
            elif order_by.split(' ')[0] == 'MiddleName':
                order_attr = getattr(Student, 'MiddleName')
            elif order_by.split(' ')[0] == 'Grade':
                order_attr = getattr('average_grade')
            elif order_by.split(' ')[0] == 'Batch':
                order_attr = getattr(Metadata, 'Batch')
            # else:
            #     if ' ' in order_by:
            #         order_query = filter_query.order_by(desc(Course.CourseCode), desc(Metadata.Year), desc(Class.Section))
            #     else:
            #         order_query = filter_query.order_by(Course.CourseCode, Metadata.Year, Class.Section)

            # # Check if order_by contains space
            # if not order_by.split(' ')[0] == "ClassName":
            if ' ' in order_by:
                order_query = filter_query.order_by(desc(order_attr))
            else:
                order_query = filter_query.order_by(order_attr)
        else:
            print("NO ORDER")
            # Apply default sorting
            order_query = filter_query.order_by(desc(Metadata.Batch), ('average_grade'))
        
        total_count = order_query.group_by(Student.StudentId, Metadata.Batch).count()
        student_grade_main_query = order_query.group_by(Student.StudentId, Metadata.Batch).offset(skip).limit(top).all()
        
        if student_grade_main_query:
            list_data_top_performer_student = []

            for data in student_grade_main_query:
                dict_student_class_grade = {
                    'StudentId': data[0],
                    'StudentNumber': data[1],
                    'LastName': data[2],
                    'FirstName': data[3],
                    'MiddleName': data[4],
                    'Batch': data[5],
                    'Grade': round(data[6], 2)
                }

                list_data_top_performer_student.append(dict_student_class_grade)

                    # Add the student number to the set of seen numbers
        return  jsonify({'result': list_data_top_performer_student, 'count': total_count})
        # else:
        #     return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None

    #     if data_top_performer_student:
    #         list_top_performer = []
    #         for data in data_top_performer_student:
                
    #             dict_student_class_grade = {
    #                 'StudentId': data[0],
    #                 'StudentNumber': data[1],
    #                 'LastName': data[2],
    #                 'FirstName': data[3],
    #                 'MiddleName': data[4],
    #                 'Batch': data[5],
    #                 'Grade': round(data[6], 2)
    #             }
                
    #             print('dict_student_class_grade: ', dict_student_class_grade)
    #             list_top_performer.append(dict_student_class_grade)
            
    #         return jsonify(list_top_performer)
    
    #     # data_top_performer_student = (
    #     #     db.session.query(
    #     #         ClassSubject,
    #     #         StudentClassSubjectGrade,
    #     #         StudentClassGrade,
    #     #         Student,
    #     #         Course,
    #     #         Class,
    #     #         Metadata
    #     #     )
    #     #     .join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
    #     #     .join(Class, Class.ClassId == ClassSubject.ClassId)
    #     #     .join(Metadata, Metadata.MetadataId == Class.MetadataId)
    #     #     .join(StudentClassGrade, StudentClassSubjectGrade.StudentId == StudentClassGrade.StudentId)
    #     #     .join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId)
    #     #     .join(Course, Course.CourseId == Metadata.CourseId)
    #     #     .filter(ClassSubject.FacultyId == str_teacher_id)
    #     #     .order_by(desc(Metadata.Batch), (StudentClassGrade.Grade))
    #     #     .limit(20).all()
    #     # )

    #     # if data_top_performer_student:
    #     #     list_data_top_performer_student = []
    #     #     seen_student_numbers = set()  # To keep track of seen student numbers
    #     #     added_count = 0  # To count the number of added objects

    #     #     for top_performer_student in data_top_performer_student:
    #     #         student_number = top_performer_student.Student.StudentNumber

    #     #         # Check if we have already seen this student number
    #     #         if student_number not in seen_student_numbers:
    #     #             class_name = f"{top_performer_student.Course.CourseCode} {top_performer_student.Metadata.Year}-{top_performer_student.Class.Section}"
    #     #             full_name = f"{top_performer_student.Student.LastName}, {top_performer_student.Student.FirstName} {top_performer_student.Student.MiddleName}"
    #     #             dict_pass_fail_rate = {
    #     #                 'StudentNumber': student_number,
    #     #                 'StudentName': full_name,
    #     #                 'Grade': top_performer_student.StudentClassGrade.Grade,
    #     #                 'Batch': top_performer_student.Metadata.Batch,
    #     #                 'Class': class_name,
    #     #                 'TeacherNum': top_performer_student.ClassSubject.FacultyId
    #     #             }

    #     #             list_data_top_performer_student.append(dict_pass_fail_rate)

    #     #             # Add the student number to the set of seen numbers
    #     #             seen_student_numbers.add(student_number)

    #     #             added_count += 1  # Increment the added count

    #     #             # Check if we have added the desired number of objects
    #     #             if added_count >= count:
    #     #                 break  # Exit the loop if count is reached

            



def getStudentClassSubjectGrade(str_teacher_id, skip, top, order_by, filter):
    print('str_teacher_id: ', str_teacher_id)
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
        filter_conditions.append(
            ClassSubject.FacultyId == str_teacher_id
        )

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
                desc(Course.CourseCode), desc(Metadata.Batch), desc(Metadata.Year), desc(Metadata.Semester), Student.LastName
            )

        # Check if order_query and filter query exists:

        # # Apply skip and top
        # result_all = order_query.all()
        # # print('result_all: ', result_all)
        # result = result_all[skip: skip + top]
        # total_count = order_query.count()
        
        total_count = order_query.count()
        result = order_query.offset(skip).limit(top).all()
        
        print('result: ', result)
        

        if result:
            list_data_class_subject_grade = []
            unique_classes = set()
     
            for class_subject_grade in result:
               
                class_name = f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Metadata.Year}-{class_subject_grade.Class.Section}"

                dict_class_subject_grade = {
                    'StudentId': class_subject_grade.Student.StudentId,
                    'StudentNumber': class_subject_grade.Student.StudentNumber,
                    'LastName': class_subject_grade.Student.LastName,
                    'FirstName': class_subject_grade.Student.FirstName,
                    'MiddleName': class_subject_grade.Student.MiddleName,
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
        print("ERROR: ", e)
        # Log the exception or handle it appropriately
        return None


# def getStudentClassSubjectGrade2(str_teacher_id, skip, top, order_by, filter):
#     try:
#         current_year = datetime.datetime.now().year

#         stud_class_grade_query = (
#             db.session.query(
#                 ClassSubject,
#                 StudentClassSubjectGrade,
#                 Subject,
#                 Class,
#                 Metadata,
#                 Course,
#                 Student
#             )
#             .join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
#             .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
#             .join(Class, Class.ClassId == ClassSubject.ClassId)
#             .join(Metadata, Metadata.MetadataId == Class.MetadataId)
#             .join(Course, Course.CourseId == Metadata.CourseId)
#             .join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId)
#             # Student Class Grade
#             # .filter(ClassSubject.FacultyId == str_teacher_id, Metadata.Batch >= current_year-4)
#         )

#         filter_conditions = []
#         # Split filter string by 'and'
#         # append the str_teacher_id
#         if filter:
#             filter_parts = filter.split(' and ')
#             for part in filter_parts:
#                 # Check if part has to lower in value
#                 if '(tolower(' in part:
#                     # Extracting column name and value
#                     column_name = part.split("(")[3].split(")")[0]
#                     value = part.split("'")[1]
#                     column_str = None
#                     print('column_name: ', column_name)
#                     print('value: ', value)
                    
#                     if column_name.strip() == 'StudentNumber':
#                         column_str = getattr(Student, 'StudentNumber')
#                     elif column_name.strip() == 'StudentName':
#                         column_str = getattr(Student, 'StudentName')
#                     elif column_name.strip() == 'Class':
#                         split_values = value.split(' ')
                        
#                         if len(split_values) >= 2:
#                             # Check split values if have a number
#                             if any(char.isdigit() for char in split_values[-1]):
#                                 batch_section = split_values[-1]
#                                 course_code = ' '.join(split_values[:-1])
#                                 column_arr_1 = getattr(Course, 'CourseCode')
#                                 year, section = None, None
                                
#                                 if '-' in batch_section:
#                                     year, section = batch_section.split('-')
#                                     if section:
#                                         column_arr_3 = getattr(Class, 'Section')
#                                     column_arr_2 = getattr(Metadata, 'Year')
#                                 else:
#                                     year = batch_section
#                                     column_arr_2 = getattr(Metadata, 'Year')
#                             else:
#                                 course_code = ' '.join(split_values)
#                                 year, section = None, None
#                                 column_arr_1 = getattr(Course, 'CourseCode')

#                             # Append column_arr_1
#                             filter_conditions.append(
#                                 func.lower(column_arr_1).like(f'%{split_values[0]}%')
#                             )
#                             # Check if year then append
#                             if year:
#                                 filter_conditions.append(Metadata.Year == int(year))
                                
#                             if section:
#                                 filter_conditions.append(
#                                     Class.Section == int(section)
#                                 )
#                             continue
#                         elif len(split_values) == 1:
#                             course_code, year, section = None, None, None
#                             # check if value contains "-" and digit in it
#                             if '-' in value and any(x.isdigit() for x in value):
#                                 year, section = value.split('-')
#                                 column_arr_2 = Metadata.Year
#                                 column_arr_3 = Class.Section
#                             else:
#                                 course_code = value
#                                 column_arr_1 = getattr(Course, 'CourseCode')
                            
#                             if course_code:
#                                 filter_conditions.append(column_arr_1.like(f'%{course_code.upper()}%'))

#                             if year:
#                                 filter_conditions.append(
#                                     column_arr_2 == int(year)
#                                 )
                            
#                             if section:
#                                 filter_conditions.append(
#                                     column_arr_3 == int(section)
#                                 )
#                             continue  
                 
#                     if column_str:
#                         # Append column_str
#                         filter_conditions.append(
#                             func.lower(column_str).like(f'%{value}%')
#                         )
#                 else:
#                     # column_name = part[0][1:]  # Remove the opening '('
#                     column_name, value = [x.strip() for x in part[:-1].split("eq")]
#                     column_name = column_name[1:]
                    
#                     column_num = None
#                     int_value = value.strip(')')

#                     if not int_value.isdigit():
#                         int_value = 0
                    
#                     if column_name.strip() == 'Year':
#                         column_num = Metadata.Year
#                     elif column_name.strip() == 'Batch':
#                         column_num = Metadata.Batch
#                     elif column_name.strip() == 'Semester':
#                         column_num = Metadata.Semester
                    
#                     if column_num:
#                         # Append column_num
#                         filter_conditions.append(
#                             column_num == int_value
#                         )
                    
#         filter_query = stud_class_grade_query.filter(and_(*filter_conditions))

#         print('ORDER BY: ', order_by)

#         # ...

#         if order_by:
#             if order_by.split(' ')[0] == 'StudentNumber':
#                 print("STUDENT NUMBER")
#                 order_attr = getattr(Student, order_by.split(' ')[0])
#             elif order_by.split(' ')[0] == "StudentName":
#                 order_attr = getattr(Student, 'Name')
#             elif order_by.split(' ')[0] == 'Grade':
#                 order_attr = getattr(StudentClassSubjectGrade, order_by.split(' ')[0])
#             elif order_by.split(' ')[0] == 'SubjectCode':
#                 print("SUBJECT CODE")
#                 order_attr = getattr(Subject, order_by.split(' ')[0])
#             elif order_by.split(' ')[0] == 'Batch':
#                 print("BATCH")
#                 order_attr = getattr(Class, order_by.split(' ')[0])
#             elif order_by.split(' ')[0] == 'Semester':
#                 print("SEMESTER")
#                 order_attr = getattr(Class, order_by.split(' ')[0])
#             else:
#                 order_by.split(' ')[0] == "Class"
#                 print("CLASS")
#                 order_attr = getattr(Class, order_by.split(' ')[0])
         

#             # Check if order_by contains space
#             if ' ' in order_by:
#                 print("INSIDE SPACE")
#                 second_query = first_query.order_by(desc(order_attr)).all()
#                 print('second_query: ', second_query)
#             else:
#                 print("NO SPACE")
#                 second_query = first_query.order_by(order_attr).all()
#                 print('second_query: ', second_query)
#         else:
#             # ...

#             second_query = first_query.order_by(desc(Course.CourseCode), desc(Metadata.Batch), desc(Metadata.Year), desc(Metadata.Semester), Student.Name).all()
            
#         total_count = (
#             db.session.query(
#                 ClassSubject,
#                 StudentClassSubjectGrade,
#                 Subject,
#                 Class,
#                 Course,
#                 Student
#             )
#             .join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
#             .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
#             .join(Class, Class.ClassId == ClassSubject.ClassId)
#             .join(Course, Course.CourseId == Metadata.CourseId)
#             .join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId)
#             .filter(ClassSubject.FacultyId == str_teacher_id, Metadata.Batch >= current_year-4)
#             .order_by(desc(Course.CourseCode), desc(Metadata.Batch), desc(Metadata.Year), desc(Metadata.Semester), Student.Name).count()
#         )

#         if second_query:
#             list_data_class_subject_grade = []
#             unique_classes = set()
     
#             for class_subject_grade in second_query:
               
#                 class_name = f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Metadata.Year}-{class_subject_grade.Class.Section}"

#                 dict_class_subject_grade = {
#                     'StudentId': class_subject_grade.Student.StudentId,
#                     'StudentNumber': class_subject_grade.Student.StudentNumber,
#                     'StudentName': class_subject_grade.Student.Name,
#                     'Class': class_name,
#                     'Batch': class_subject_grade.Metadata.Batch,
#                     'Semester': class_subject_grade.Metadata.Semester,
#                     'Grade': class_subject_grade.StudentClassSubjectGrade.Grade,
#                     'SubjectCode': class_subject_grade.Subject.SubjectCode
#                 }

#                 list_data_class_subject_grade.append(dict_class_subject_grade)
#                 unique_classes.add(class_name)

#             sorted_unique_classes = sorted(unique_classes)
      
#             # Return the list of class grades, the classes, and pagination information
#             return jsonify({'result':list_data_class_subject_grade, 'count': total_count, 'classes': list(sorted_unique_classes)})
#         else:
#             return {'ClassSubjectGrade': [], 'Classes': [], 'currentPage': 1, 'totalPages': 0, 'totalItems': 0}

#     except Exception as e:
#         # Log the exception or handle it appropriately
#         return None

# RENDER THIS IN FRONTEND


def getAllClass(str_teacher_id):
    try:
        # Get LatestBatchSemester.IsGradeFinalized == True
        latest_batch_semester = db.session.query(LatestBatchSemester).filter(LatestBatchSemester.IsGradeFinalized == False, LatestBatchSemester.IsEnrollmentStarted == True).order_by(desc(LatestBatchSemester.created_at)).first()
        
        print('latest_batch_semester: ', latest_batch_semester.Batch)
        
        # current_year = datetime.datetime.now().year

        data_class_subject_grade_handle = (
            db.session.query(
                ClassSubject,
                Class, Course, Metadata
            )
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .filter(ClassSubject.FacultyId == str_teacher_id, Metadata.Batch == latest_batch_semester.Batch, Class.IsGradeFinalized == False)
            .order_by(desc(Metadata.CourseId), Metadata.Year, Class.Section)
            .all()
        )

        if data_class_subject_grade_handle:
            list_classes = []
            seen_class_name = set()  # Initialize a set to track seen ClassIds

            for class_subject_grade in data_class_subject_grade_handle:
                class_name = f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Metadata.Year}-{class_subject_grade.Class.Section}"

                # Check if the ClassId is not in the seen_class_name set
                if class_name not in seen_class_name:
                    # Get the class name
                    class_obj = {
                        'ClassId': class_subject_grade.Class.ClassId,
                        'ClassName': class_name
                    }

                    # Add class_name to the seen_class_name set
                    seen_class_name.add(class_name)

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
                ClassGrade, Class, Course, Metadata
            )
            .join(Class, Class.ClassId == ClassGrade.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .filter(ClassGrade.ClassId == class_id)
            .first()
        )
        
        print('class_grade: ', class_grade)
        if class_grade:
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
            print('dict_class_grade: ', dict_class_grade)
            list_grade = []
            for i in range(1, class_grade.Metadata.Year+1):

                batch = class_grade.Metadata.Batch - class_grade.Metadata.Year + i

                class_grade_result = (
                    db.session.query(
                        Class,
                        ClassGrade,
                        Metadata
                    )
                    .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                    .join(Metadata, Metadata.MetadataId == Class.MetadataId)
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
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
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
                # Check if Grade is not 0 or NoneTypew
                if gpa.StudentClassGrade.Grade == 0 or gpa.StudentClassGrade.Grade is None:
                    continue
                else:
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
        print("ERROR: ", e )
        # Handle the exception here, e.g., log it or return an error response
        return None


def getFacultyData(str_teacher_id):
    try:
        data_faculty = (
            db.session.query(Faculty).filter(
                Faculty.FacultyId == str_teacher_id).first()
        )

        if data_faculty:
            middle_name = data_faculty.MiddleName if data_faculty.MiddleName else ""
            full_name = f"{data_faculty.LastName}, {data_faculty.FirstName} {middle_name}"
            
            dict_faculty_data = {
                "TeacherId": data_faculty.FacultyId,
                'FacultyType': data_faculty.FacultyType,
                "Name": full_name,
                "ResidentialAddress": data_faculty.ResidentialAddress,
                "Email": data_faculty.Email,
                "MobileNumber": data_faculty.MobileNumber,
                "Gender": "Male" if data_faculty.Gender == 1 else "Female",
            }

            return (dict_faculty_data)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def updateFacultyData(str_teacher_id, number, residential_address):
    try:
        # if not re.match(r'^[\w\.-]+@[\w\.-]+$', email):
        #     return {"type": "email", "status": 400}

        if not re.match(r'^09\d{9}$', number):
            return {"type": "mobile", "status": 400}

        if residential_address is None or residential_address.strip() == "":
            return {"type": "residential", "status": 400}
        
        # Update the student data in the database
        data_faculty = db.session.query(Faculty).filter(
            Faculty.FacultyId == str_teacher_id).first()
        
        if data_faculty:
            # data_faculty.Email = email
            data_faculty.MobileNumber = number
            data_faculty.ResidentialAddress = residential_address
            db.session.commit()

            return {"message": "Data updated successfully", "number": number, "residential_address": residential_address, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}


def updatePassword(str_teacher_id, password, new_password, confirm_password):
    try:
        data_faculty = db.session.query(Faculty).filter(Faculty.FacultyId == str_teacher_id).first()

        if data_faculty:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_faculty.password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(
                    new_password)
                data_faculty.password = new_hashed_password
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

            # Now you can use the modified_section_code as needed in your code
            student_data = (
                db.session.query(Student,  StudentClassSubjectGrade, ClassSubject, Class, Subject, Course, Metadata)
                .join(StudentClassSubjectGrade, StudentClassSubjectGrade.StudentId == Student.StudentId)
                .join(ClassSubject, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId)
                .join(Class, Class.ClassId == ClassSubject.ClassId)
                .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
                .join(Course, Course.CourseId == Metadata.CourseId)
                .filter(Student.StudentNumber == student_number, Metadata.Year == year, Class.Section == section, Metadata.Batch == batch, Metadata.Semester == semester,  Subject.SubjectCode == subject_code)
                .order_by(desc(Student.Name), desc(Metadata.Year), desc(Class.Section), desc(Metadata.Batch))
                .first()
            )
            
            if(student_data.Class.IsGradeFinalized==False):
                # Update the Class isGradeFinalized to False
                student_data.StudentClassSubjectGrade.Grade = grade
                
                # Save only but dont commit in database
                db.session.add(student_data.StudentClassSubjectGrade)
            else:
                return jsonify({'error': 'The grade has been finalized. Contact admin if there is an issue exist'}), 500
        # If all data is updated successfully then commit the data
        db.session.commit()
        return jsonify({'success': 'File uploaded and data processed successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'An error occurred while processing the file'}), 500


# def getAllClassAverage(str_teacher_id):
#     try:
#         current_year = datetime.datetime.now().year

#         data_class_grade_handle = (
#             db.session.query(
#                 ClassSubject,
#                 Class,
#                 ClassGrade,
#                 Course,
#             )
#             .join(Class, ClassSubject.ClassId == Class.ClassId)
#             .join(ClassGrade, Class.ClassId == ClassGrade.ClassId)
#             .join(Course, Metadata.CourseId == Course.CourseId)
#             .filter(ClassSubject.TeacherId == str_teacher_id, Class.Batch == current_year-1)
#             .distinct(Metadata.CourseId, Class.Year, Class.Batch)
#             # I Limit this into 8 because teacher cannot have many classes and the data sets made are distributed almost all of them
#             .limit(6)
#             # Once the data sets is fixed this can replace the previous line
#             # .all()
#         )

#         if data_class_grade_handle:
#             list_data_class_grade = []

#             for class_grade_handle in data_class_grade_handle:
#                 # Calculate class name
#                 class_name = f"{class_grade_handle.Course.CourseId} {class_grade_handle.Class.Year}-{class_grade_handle.Class.Section} ({class_grade_handle.Class.Batch})"

#                 dict_class_grade_handle = {
#                     'Class': class_name,
#                     'Year': class_grade_handle.Class.Year,
#                     'Section': class_grade_handle.Class.Section,
#                     'Batch': class_grade_handle.Class.Batch,
#                     'Grade': class_grade_handle.ClassGrade.Grade
#                 }

#                 list_data_class_grade.append(dict_class_grade_handle)

#             # Return the list of class grades and the lowest/highest grades dictionary
#             return (list_data_class_grade)
#         else:
#             return None

#     except Exception as e:
#         # Handle the exception here, e.g., log it or return an error response
#         return None
