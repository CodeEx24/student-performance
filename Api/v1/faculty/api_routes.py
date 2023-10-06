# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import Faculty

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required

from .utils import getSubjectCount, getHighLowAverageClass, getAllClassAverageWithPreviousYear, getPassFailRates, getTopPerformerStudent, getStudentClassSubjectGrade, getAllClass, getClassPerformance, updateFacultyData, getFacultyData, updatePassword, getStudentPerformance, getCurrentUser

import os


faculty_api = Blueprint('faculty_api', __name__)

# Api/v1/faculty/api_routes.py
# Define a function to get the current faculty


@faculty_api.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        teacher = Faculty.query.filter_by(Email=email).first()
        if teacher and check_password_hash(teacher.Password, password):
            # Successfully authenticated
            session['user_id'] = teacher.TeacherId
            session['user_role'] = 'faculty'
            return redirect(url_for('facultyHome'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('facultyLogin'))


# ===================================================
# TESTING AREA
@faculty_api.route('/profile', methods=['GET'])
@role_required('faculty')
def profile():
    faculty = getCurrentUser()
    if faculty:
        return jsonify(faculty.to_dict())
    else:
        return render_template('404.html'), 404

# ===================================================


# Getting the user (faculty) data
@faculty_api.route('/', methods=['GET'])
@role_required('faculty')
def facultyData():
    faculty = getCurrentUser()
    if faculty:
        json_faculty_data = getFacultyData(faculty.TeacherId)
        if json_faculty_data:
            return (json_faculty_data)
        else:
            return jsonify(message="No user data available")
    else:
        return render_template('404.html'), 404


# Update the details of the faculty
@faculty_api.route('/details/update', methods=['GET', 'POST'])
@role_required('faculty')
def updateDetails():
    faculty = getCurrentUser()
    if faculty:
        if request.method == 'POST':
            email = request.json.get('email')
            number = request.json.get('number')
            residential_address = request.json.get('residential_address')

            json_result = updateFacultyData(
                faculty.TeacherId, email, number, residential_address)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('facultyLogin'))
    else:
        return render_template('404.html'), 404


# Change the password of the user (faculty)
@faculty_api.route('/change/password', methods=['POST'])
@role_required('faculty')
def changePassword():
    faculty = getCurrentUser()
    if faculty:
        if request.method == 'POST':
            password = request.json.get('password')
            new_password = request.json.get('new_password')
            confirm_password = request.json.get('confirm_password')

            json_result = updatePassword(faculty.TeacherId, password, new_password, confirm_password)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404


# Getting the Highest and Lowest Class Average
@faculty_api.route('/class-statistics', methods=['GET'])
@role_required('faculty')
def classAverageAndSubjectCount():
    faculty = getCurrentUser()
    if faculty:
        json_high_low_class = getHighLowAverageClass(faculty.TeacherId)
        json_subject_count = getSubjectCount(faculty.TeacherId)
        if json_high_low_class and json_subject_count is not None:
            return ({**json_high_low_class, **json_subject_count})
        else:
            return jsonify(message="Something went wrong")
    else:
        return render_template('404.html'), 404


# All class average per year
@faculty_api.route('/class-average', methods=['GET'])
@role_required('faculty')
def allClassAverages():
    faculty = getCurrentUser()
    if faculty:
        json_average_class = getAllClassAverageWithPreviousYear(faculty.TeacherId)

        if json_average_class:
            return (json_average_class)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Get the pass and failed counts to the facultys subject
@faculty_api.route('/pass-fail', methods=['GET'])
@role_required('faculty')
def passFailRates():
    faculty = getCurrentUser()
    if faculty:
        json_average_class = getPassFailRates(faculty.TeacherId)

        if json_average_class:
            return (json_average_class)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the top performer student
@faculty_api.route('/top-student', methods=['GET'])
@role_required('faculty')
def topPerformerStudent():
    faculty = getCurrentUser()
    if faculty:
        json_top_performer_student = getTopPerformerStudent(
            faculty.TeacherId, 10)

        if json_top_performer_student:
            return (json_top_performer_student)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the student subject grade in a class
@faculty_api.route('/class-subject-grade', methods=['GET'])
@role_required('faculty')
def studentClassSubjectGrade():
    faculty = getCurrentUser()
    if faculty:
        json_class_subject_grade = getStudentClassSubjectGrade(
            faculty.TeacherId)

        if json_class_subject_grade:
            return (json_class_subject_grade)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Fetch all class handle
@faculty_api.route('/all-class', methods=['GET'])
@role_required('faculty')
def allClass():
    faculty = getCurrentUser()
    if faculty:
        json_class_subject_grade = getAllClass(
            faculty.TeacherId)

        if json_class_subject_grade:
            return (json_class_subject_grade)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting all class performance of the specifc class
@faculty_api.route('/class-performance/<int:id>', methods=['GET', 'POST'])
@role_required('faculty')
def classPerformance(id):
    faculty = getCurrentUser()
    if faculty:
        json_class_performance = getClassPerformance(id)

        if json_class_performance:
            return (json_class_performance)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the specific student performance
@faculty_api.route('/student/performance/<string:id>', methods=['GET', 'POST'])
@role_required('faculty')
def studentPerformance(id):
    faculty = getCurrentUser()
    if faculty:
        json_student_performance = getStudentPerformance(id)

        if json_student_performance:
            return (json_student_performance)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
