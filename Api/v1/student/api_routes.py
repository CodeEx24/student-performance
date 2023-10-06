# api/api_routes.py
from flask import jsonify
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from sqlalchemy import desc
from werkzeug.security import check_password_hash
from models import Student
import os

from decorators.auth_decorators import role_required

# FUNCTIONS IMPORT
from .utils import getStudentGpa, getStudentPerformance, getCoursePerformance, getLatestSubjectGrade, getOverallGrade, getSubjectsGrade, getStudentData, updateStudentData, updatePassword, getCurrentUser

student_api = Blueprint('student_api', __name__)

# Api/v1/student/api_routes.py

# ===================================================
# TESTING AREA

# Student User Log in
@student_api.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        student = Student.query.filter_by(Email=email).first()
        if student and check_password_hash(student.Password, password):
            # Successfully authenticated
            # access_token = create_access_token(identity=student.StudentId)
            # refresh_token = create_refresh_token(identity=student.StudentId)
            session['user_id'] = student.StudentId
            session['user_role'] = 'student'
            
            # session['student_id'] = student.StudentId
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"message": "Invalid email or password"}), 401
    return jsonify({"message": "Method not allowed"}), 405



@student_api.route('/profile', methods=['GET'])
@role_required('student')
def profile():
    student = getCurrentUser()
    if student:
        return jsonify(student.to_dict())
    else:
        flash('User not found', 'danger')
        return redirect(url_for('student_api.login'))

# Getting the overall GPA
@student_api.route('/overall-gpa', methods=['GET'])
@role_required('student')
def overallGrade():
    student = getCurrentUser()
    if student:
        json_overall_gpa = getOverallGrade(student.StudentId)

        if json_overall_gpa:
            return (json_overall_gpa)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404

# ============================================================

# Getting the user details
@student_api.route('/', methods=['GET'])
@role_required('student')
def studentData():
    student = getCurrentUser()
    if student:
        json_student_data = getStudentData(student.StudentId)
        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404


# Updating the user details
@student_api.route('/details/update', methods=['POST'])
@role_required('student')
def updateDetails():
    student = getCurrentUser()
    if student:
        if request.method == 'POST':
            email = request.json.get('email')
            number = request.json.get('number')
            residentialAddress = request.json.get('residentialAddress')

            json_result = updateStudentData(
                student.StudentId, email, number, residentialAddress)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    # else:
    #     return render_template('404.html'), 404


# Changing the password of the user
@student_api.route('/change/password', methods=['POST'])
@role_required('student')
def changePassword():
    student = getCurrentUser()
    if student:
        if request.method == 'POST':
            password = request.json.get('password')
            new_password = request.json.get('new_password')
            confirm_password = request.json.get('confirm_password')

            json_result = updatePassword(
                student.StudentId, password, new_password, confirm_password)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404


# Latest GPA of the Student in Class
@student_api.route('/gpa', methods=['GET'])
@role_required('student')
def studentGpa():
    student = getCurrentUser()
    if student:
        json_student_gpa = getStudentGpa(student.StudentId)
        
        if json_student_gpa is not None:
            return jsonify(json_student_gpa)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404


# Performance of Student Over Time
@student_api.route('/performance', methods=['GET'])
@role_required('student')
def performance():
    student = getCurrentUser()
    if student:
        json_performance_data = getStudentPerformance(student.StudentId)

        if json_performance_data:
            return (json_performance_data)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404


# Getting Previous Subjects Grade
@student_api.route('/previous-grade', methods=['GET'])
@role_required('student')
def previousGrade():
    student = getCurrentUser()
    if student:

        json_previous_grade = getLatestSubjectGrade(student.StudentId)

        if json_previous_grade:
            return (json_previous_grade)
        else:
            return jsonify(message="No Grades data available")
    else:
        return render_template('404.html'), 404

# Current Course Performance
@student_api.route('/course-performance', methods=['GET'])
@role_required('student')
def coursePerformance():
    student = getCurrentUser()
    if student:
        json_course_performance = getCoursePerformance(student.StudentId)

        if json_course_performance:
            return (json_course_performance)
        else:
            return render_template('404.html'), 404


   
# Getting the subjects grades
@student_api.route('/grades', methods=['GET'])
@role_required('student')
def subjectsGrade():
    student = getCurrentUser()
    if student:
        json_subjects_grade = getSubjectsGrade(student.StudentId)

        if json_subjects_grade:
            return (json_subjects_grade)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404
