from models import CourseGrade, Course, UniversityAdmin, Faculty, Student, SystemAdmin, db
from collections import defaultdict
from sqlalchemy import func
from static.js.utils import convertGradeToPercentage
from flask import jsonify, session

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

        print('data_course_grade: ', data_course_grade)
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
            print('formatted_data: ', formatted_data)
            print('list_course: ', list_course)
            return jsonify({'success': True, 'list_course': list_course, 'course_performance': formatted_data})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return e

def getCurrentUser(role):
    current_user_id = session.get('user_id')
    if role == 'student': 
        return Student.query.get(current_user_id)
    elif role == 'faculty':
        return Faculty.query.get(current_user_id)
    elif role == 'universityAdmin':
        return UniversityAdmin.query.get(current_user_id)
    elif role == 'systemAdmin':
        return SystemAdmin.query.get(current_user_id)