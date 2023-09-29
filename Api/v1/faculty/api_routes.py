# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import Faculty

from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
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
            refresh_token = create_refresh_token(identity=teacher.TeacherId)
            session['access_token'] = access_token
            session['refresh_token'] = refresh_token
            session['user_role'] = 'faculty'
            return redirect(url_for('facultyHome'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('facultyLogin'))


# ===================================================
# TESTING AREA
@faculty_api.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        return jsonify(faculty.to_dict())
    else:
        return render_template('404.html'), 404

# ===================================================


# Getting the user (faculty) data
@faculty_api.route('/', methods=['GET'])
@jwt_required()
def facultyData():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        json_faculty_data = getFacultyData(current_user_id)
        if json_faculty_data:
            return (json_faculty_data)
        else:
            return jsonify(message="No user data available")
    else:
        return render_template('404.html'), 404


# Update the details of the faculty
@faculty_api.route('/details/update', methods=['GET', 'POST'])
@jwt_required()
def updateDetails():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        if request.method == 'POST':
            email = request.json.get('email')
            number = request.json.get('number')
            residential_address = request.json.get('residential_address')

            json_result = updateFacultyData(
                current_user_id, email, number, residential_address)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('facultyLogin'))
    else:
        return render_template('404.html'), 404


# Change the password of the user (faculty)
@faculty_api.route('/change/password', methods=['POST'])
@jwt_required()
def changePassword():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        if request.method == 'POST':
            password = request.json.get('password')
            new_password = request.json.get('new_password')
            confirm_password = request.json.get('confirm_password')

            json_result = updatePassword(current_user_id, password, new_password, confirm_password)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404


# Getting the Highest and Lowest Class Average
@faculty_api.route('/class-statistics', methods=['GET'])
@jwt_required()
def classAverageAndSubjectCount():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        json_high_low_class = getHighLowAverageClass(current_user_id)
        json_subject_count = getSubjectCount(current_user_id)
        if json_high_low_class and json_subject_count is not None:
            return ({**json_high_low_class, **json_subject_count})
        else:
            return jsonify(message="Something went wrong")
    else:
        return render_template('404.html'), 404


# All class average per year
@faculty_api.route('/class-average', methods=['GET'])
@jwt_required()
def allClassAverages():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        json_average_class = getAllClassAverageWithPreviousYear(current_user_id)

        if json_average_class:
            return (json_average_class)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Get the pass and failed counts to the facultys subject
@faculty_api.route('/pass-fail', methods=['GET'])
@jwt_required()
def passFailRates():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        json_average_class = getPassFailRates(current_user_id)

        if json_average_class:
            return (json_average_class)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the top performer student
@faculty_api.route('/top-student', methods=['GET'])
@jwt_required()
def topPerformerStudent():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        json_top_performer_student = getTopPerformerStudent(
            current_user_id, 10)

        if json_top_performer_student:
            return (json_top_performer_student)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the student subject grade in a class
@faculty_api.route('/class-subject-grade', methods=['GET'])
@jwt_required()
def studentClassSubjectGrade():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        json_class_subject_grade = getStudentClassSubjectGrade(
            current_user_id)

        if json_class_subject_grade:
            return (json_class_subject_grade)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Fetch all class handle
@faculty_api.route('/all-class', methods=['GET'])
@jwt_required()
def allClass():
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        json_class_subject_grade = getAllClass(
            current_user_id)

        if json_class_subject_grade:
            return (json_class_subject_grade)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting all class performance of the specifc class
@faculty_api.route('/class-performance/<int:id>', methods=['GET', 'POST'])
@jwt_required()
def classPerformance(id):
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        json_class_performance = getClassPerformance(id)

        if json_class_performance:
            return (json_class_performance)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the specific student performance
@faculty_api.route('/student/performance/<string:id>', methods=['GET', 'POST'])
@jwt_required()
def studentPerformance(id):
    current_user_id = get_jwt_identity()
    role = session.get('user_role')
    faculty = Faculty.query.get(current_user_id)
    if faculty and role=="faculty":
        json_student_performance = getStudentPerformance(id)

        if json_student_performance:
            return (json_student_performance)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
