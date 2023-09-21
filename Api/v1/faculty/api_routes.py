# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import Faculty

from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from decorators.auth_decorators import facultyRequired

from .utils import getSubjectCount, getHighLowAverageClass, getAllClassAverageWithPreviousYear, getPassFailRates, getTopPerformerStudent, getStudentClassSubjectGrade, getAllClass, getClassPerformance, updateFacultyData, getFacultyData, updatePassword, getStudentPerformance

import os

# Access API keys from environment variables
WEBSITE1_API_KEY = os.getenv('WEBSITE1_API_KEY')
WEBSITE2_API_KEY = os.getenv('WEBSITE2_API_KEY')
WEBSITE3_API_KEY = os.getenv('WEBSITE3_API_KEY')
WEBSITE4_API_KEY = os.getenv('WEBSITE4_API_KEY')
WEBSITE5_API_KEY = os.getenv('WEBSITE5_API_KEY')
faculty_api_key = os.getenv('FACULTY_API_KEY')


API_KEYS = {
    'website1': WEBSITE1_API_KEY,
    'website2': WEBSITE2_API_KEY,
    'website3': WEBSITE3_API_KEY,
    'website4': WEBSITE4_API_KEY,
    'website5': WEBSITE5_API_KEY,
    'faculty_key': faculty_api_key
}

faculty_api = Blueprint('faculty_api', __name__)

# Api/v1/faculty/api_routes.py


@faculty_api.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        teacher = Faculty.query.filter_by(Email=email).first()
        if teacher and check_password_hash(teacher.Password, password):
            # Successfully authenticated
            access_token = create_access_token(identity=teacher.TeacherId)
            session['access_token'] = access_token
            session['user_role'] = 'faculty'
            session['teacher_number'] = teacher.TeacherNumber
            return redirect(url_for('facultyHome'))
        else:
            flash('Invalid email or password', 'danger')
    return redirect(url_for('facultyLogin'))


# ===================================================
# TESTING AREA
@faculty_api.route('/profile', methods=['GET'])
@facultyRequired
@jwt_required()
def profile():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        current_user_id = get_jwt_identity()
        faculty = Faculty.query.get(current_user_id)
        if faculty:
            return jsonify(faculty.to_dict())
        else:
            flash('User not found', 'danger')
            return redirect(url_for('faculty_api.login'))
    else:
        return render_template('404.html'), 404

# ===================================================


# Getting the user (faculty) data
@faculty_api.route('/', methods=['GET'])
def studentData():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_teacher_number = session.get('teacher_number')
        # student = Student.query.get(str_student_number)
        json_faculty_data = getFacultyData(str_teacher_number)

        if json_faculty_data:
            return (json_faculty_data)
        else:
            return jsonify(message="No user data available")
    else:
        return render_template('404.html'), 404


# Update the details of the faculty
@faculty_api.route('/details/update', methods=['GET', 'POST'])
def updateDetails():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        if request.method == 'POST':
            str_teacher_number = session.get('teacher_number')
            email = request.json.get('email')
            number = request.json.get('number')
            residential_address = request.json.get('residential_address')

            json_result = updateFacultyData(
                str_teacher_number, email, number, residential_address)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404


# Change the password of the user (faculty)
@faculty_api.route('/change/password', methods=['POST'])
def changePassword():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        if request.method == 'POST':
            str_teacher_number = session.get('teacher_number')
            password = request.json.get('password')
            new_password = request.json.get('new_password')
            confirm_password = request.json.get('confirm_password')

            json_result = updatePassword(
                str_teacher_number, password, new_password, confirm_password)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404


# Getting the Highest and Lowest Class Average
@faculty_api.route('/class-statistics', methods=['GET'])
def classAverageAndSubjectCount():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_teacher_number = session.get('teacher_number')

        json_high_low_class = getHighLowAverageClass(str_teacher_number)
        json_subject_count = getSubjectCount(str_teacher_number)
        if json_high_low_class and json_subject_count is not None:
            return ({**json_high_low_class, **json_subject_count})
        else:
            return jsonify(message="Something went wrong")
    else:
        return render_template('404.html'), 404


# All class average per year
@faculty_api.route('/class-average', methods=['GET'])
def allClassAverages():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_teacher_number = session.get('teacher_number')

        json_average_class = getAllClassAverageWithPreviousYear(
            str_teacher_number)

        if json_average_class:
            return (json_average_class)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Get the pass and failed counts to the facultys subject
@faculty_api.route('/pass-fail', methods=['GET'])
def passFailRates():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_teacher_number = session.get('teacher_number')

        json_average_class = getPassFailRates(str_teacher_number)

        if json_average_class:
            return (json_average_class)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the top performer student
@faculty_api.route('/top-student', methods=['GET'])
def topPerformerStudent():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_teacher_number = session.get('teacher_number')

        json_top_performer_student = getTopPerformerStudent(
            str_teacher_number, 10)

        if json_top_performer_student:
            return (json_top_performer_student)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the student subject grade in a class
@faculty_api.route('/class-subject-grade', methods=['GET'])
def studentClassSubjectGrade():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_teacher_number = session.get('teacher_number')

        json_class_subject_grade = getStudentClassSubjectGrade(
            str_teacher_number)

        if json_class_subject_grade:
            return (json_class_subject_grade)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Fetch all class handle
@faculty_api.route('/all-class', methods=['GET'])
def allClass():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        str_teacher_number = session.get('teacher_number')

        json_class_subject_grade = getAllClass(
            str_teacher_number)

        if json_class_subject_grade:
            return (json_class_subject_grade)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting all class performance of the specifc class
@faculty_api.route('/class-performance/<int:id>', methods=['GET', 'POST'])
def classPerformance(id):
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        json_class_performance = getClassPerformance(id)

        if json_class_performance:
            return (json_class_performance)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the specific student performance
@faculty_api.route('/student/performance/<string:id>', methods=['GET', 'POST'])
def studentPerformance(id):
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        json_student_performance = getStudentPerformance(id)

        if json_student_performance:
            return (json_student_performance)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
