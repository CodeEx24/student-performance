# api/api_routes.py
from flask import jsonify
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from sqlalchemy import desc
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import Student, StudentClassGrade, Class
import os

# FUNCTIONS IMPORT
from .utils import getStudentGpa, getStudentPerformance, getCoursePerformance, getLatestSubjectGrade, getOverallGrade, getSubjectsGrade, getStudentData, updateStudentData, updatePassword


# Access API keys from environment variables
WEBSITE1_API_KEY = os.getenv('WEBSITE1_API_KEY')
WEBSITE2_API_KEY = os.getenv('WEBSITE2_API_KEY')
WEBSITE3_API_KEY = os.getenv('WEBSITE3_API_KEY')
WEBSITE4_API_KEY = os.getenv('WEBSITE4_API_KEY')
WEBSITE5_API_KEY = os.getenv('WEBSITE5_API_KEY')
student_api_key = os.getenv('STUDENT_API_KEY')


API_KEYS = {
    'website1': WEBSITE1_API_KEY,
    'website2': WEBSITE2_API_KEY,
    'website3': WEBSITE3_API_KEY,
    'website4': WEBSITE4_API_KEY,
    'website5': WEBSITE5_API_KEY,
    'student_key': student_api_key
    # Add more websites and keys as needed
}

student_api = Blueprint('student_api', __name__)

# Api/v1/student/api_routes.py

# ===================================================
# TESTING AREA


@student_api.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()

    student = Student.query.get(current_user_id)
    if student:
        return jsonify(student.to_dict())
    else:
        flash('User not found', 'danger')
        return redirect(url_for('student_api.login'))

# ============================================================


# Getting the user details
@student_api.route('/', methods=['GET'])
def studentData():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_student_number = session.get('student_number')

        # student = Student.query.get(str_student_number)
        json_student_data = getStudentData(str_student_number)

        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404


# Updating the user details
@student_api.route('/details/update', methods=['POST'])
def updateDetails():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        if request.method == 'POST':
            str_student_number = session.get('student_number')
            email = request.json.get('email')
            number = request.json.get('number')
            place_of_birth = request.json.get('placeOfBirth')

            json_result = updateStudentData(
                str_student_number, email, number, place_of_birth)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404


# Changing the password of the user
@student_api.route('/change/password', methods=['POST'])
def changePassword():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        if request.method == 'POST':
            str_student_number = session.get('student_number')
            password = request.json.get('password')
            new_password = request.json.get('new_password')
            confirm_password = request.json.get('confirm_password')

            json_result = updatePassword(
                str_student_number, password, new_password, confirm_password)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404


# Student User Log in
@student_api.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        student = Student.query.filter_by(Email=email).first()
        if student and check_password_hash(student.Password, password):
            # Successfully authenticated
            access_token = create_access_token(identity=student.StudentId)
            session['access_token'] = access_token
            session['user_role'] = 'student'
            session['student_number'] = student.StudentNumber
            return redirect(url_for('studentHome'))
        else:
            flash('Invalid email or password', 'danger')
    return redirect(url_for('studentLogin'))


# Latest GPA of the Student in Class
@student_api.route('/gpa', methods=['GET'])
def studentGpa():
    # Get the API key from the request header
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_student_number = session.get('student_number')

        json_student_gpa = getStudentGpa(str_student_number)
        if json_student_gpa is not None:
            return jsonify(json_student_gpa)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404


# Performance of Student Over Time
@student_api.route('/performance', methods=['GET'])
def performance():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_student_number = session.get('student_number')

        # student = Student.query.get(studentNumber)
        json_performance_data = getStudentPerformance(str_student_number)

        if json_performance_data:
            return (json_performance_data)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404


# Current Course Performance
@student_api.route('/course-performance', methods=['GET'])
def coursePerformance():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_student_number = session.get('student_number')

        # student = Student.query.get(str_student_number)
        json_course_performance = getCoursePerformance(str_student_number)

        if json_course_performance:
            return (json_course_performance)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404


# Getting Previous Subjects Grade
@student_api.route('/previous-grade', methods=['GET'])
def previousGrade():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_student_number = session.get('student_number')

        # student = Student.query.get(str_student_number)
        json_previous_grade = getLatestSubjectGrade(str_student_number)

        if json_previous_grade:
            return (json_previous_grade)
        else:
            return jsonify(message="No Grades data available")
    else:
        return render_template('404.html'), 404


# Getting the overall GPA
@student_api.route('/overall-gpa', methods=['GET'])
def overallGrade():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_student_number = session.get('student_number')

        # student = Student.query.get(str_student_number)
        json_overall_gpa = getOverallGrade(str_student_number)

        if json_overall_gpa:
            return (json_overall_gpa)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404


# Getting the subjects grades
@student_api.route('/grades', methods=['GET'])
def subjectsGrade():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_student_number = session.get('student_number')

        # student = Student.query.get(str_student_number)
        json_subjects_grade = getSubjectsGrade(str_student_number)

        if json_subjects_grade:
            return (json_subjects_grade)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404
