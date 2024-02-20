# api/api_routes.py
from flask import jsonify
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from sqlalchemy import desc
from werkzeug.security import check_password_hash, gen_salt
from models import Student, db, OAuth2Token, CourseEnrolled, Course
from oauth2 import authorization, require_oauth
import os
import time
from authlib.integrations.flask_oauth2 import current_token

from decorators.auth_decorators import preventAuthenticated, role_required
from decorators.rate_decorators import login_decorator, resend_otp_decorator

# FUNCTIONS IMPORT
from .utils import getStudentGpa, getStudentPerformance, getCoursePerformance, getLatestSubjectGrade, getOverallGrade, getSubjectsGrade, getStudentData, updateStudentData, updatePassword, getCurrentUser, saveSessionValues, getUnitsTaken
from werkzeug.security import generate_password_hash

import random
from flask_mail import Message
from mail import mail  # Import mail from the mail.py module
import secrets
from datetime import datetime, timedelta
import re

student_api_base_url = os.getenv("STUDENT_API_BASE_URL")
student_api = Blueprint('student_api', __name__)
# from app import create_app
# Api/v1/student/api_routes.py

MAX_LOGIN_ATTEMPTS = 3

# MAIN LOGIN

@student_api.route('/login', methods=['POST'])
# @login_decorator("Too many login attempts. Please try again later")
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            
            if not email or not password:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
                return jsonify({'error': True, 'message': 'Invalid email format type'}), 401
            
            student = Student.query.filter_by(Email=email).first()
            if not student:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401
            
            if student and check_password_hash(student.Password, password):
                session['user_id'] = student.StudentId
                session['user_role'] = 'student'
                return jsonify({"success": True, "message": "Login successful"}), 200
            else:
                return jsonify({"error": True, "message": "Invalid email or password"}), 401
        except Exception as e:
            print('An exception occurred')
            return jsonify({"error": True, "message": "Invalid email or password"}), 401


# @student_api.route('/verify-otp', methods=['POST'])
# def verifyOtp():
#     if request.method == 'POST':
#         # Get the user id in session
#         # return jsonify success
#         session['user_role'] = 'student'
#         return jsonify({'success': True, "message": "OTP verified"}), 200
#     else:
#         return jsonify({'error': True, "message": 'Invalid request method'}), 400
    
    
@student_api.route('/resend-otp', methods=['POST'])
def resendOtp():
    if request.method == 'POST':
        # Check if user_id have value in session
        user_id = session.get('user_id')
        if user_id:
            session['otp'] = ''.join([str(random.randint(0, 9)) for i in range(6)])
            session['otp_expired_at'] = time.time() + (5 * 60)
            # Print the otp resend
            print('OTP Resend: ', session.get('otp'))
            return jsonify({'success': True, "message": "OTP sent successfully"}), 200
    else:
        return jsonify({'error': True, 'message': 'Invalid request method'}), 400



# @student_api.route('/login', methods=['POST'])
# def login():
#     if request.method == 'POST':
#         if 'login_attempts' not in session:
#             session['login_attempts'] = 0

#         if session['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
#             print("LOGIN REACH")
#             flash('Too many login attempts. Please try again later.')
#             return jsonify({'error': 'Too many login attempts. Please try again later.'}), 429  # 429 Too Many Requests

        
#         email = request.form['email']
#         password = request.form['password']
        
#         student = Student.query.filter_by(Email=email).first()
#         if student and check_password_hash(student.Password, password):
#             session['user_id'] = student.StudentId
#             session.pop('login_attempts', None)  # Reset login attempts upon successful login

#             # Generate an otp with 6 length and save to session. Numbers only
#             session['otp'] = ''.join([str(random.randint(0, 9)) for i in range(6)])
#             session['otp_expired_at'] = time.time() + (5 * 60)
#             print('OTP: ', session.get('otp'))
            
#             return jsonify({"message": "Login successful"}), 200
#         else:
#             session['login_attempts'] += 1
#             return jsonify({"message": "Invalid email or password"}), 401
#     else:
#         return jsonify({'error': 'Invalid request method'}), 400
    

# ===================================================
# TESTING AREA
# Step 4: Handle the form submission for requesting a password reset email
@student_api.route('/reset_password', methods=['POST'])
def forgotPassword():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': True, 'message': 'Please input an email'}), 401

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
        return jsonify({'error': True, 'message': 'Invalid email format type'}), 401
    
    # Check if email exists in the database
    student = Student.query.filter_by(Email=email).first()

    if not student:
        # Intended so the intruder cannot be able to know whether email is registered or not
        return jsonify({'success': True, 'message': 'An email with instructions to reset your password has been sent to email.'}),200
        # return jsonify({'error': True, 'message': 'Email is invalid'}), 400

    if student:
        # Generate a secure token
        token = secrets.token_hex(16)

        # Save the token and its expiration time in the database
        student.Token = token
        student.TokenExpiration = datetime.now() + timedelta(minutes=30)
        db.session.commit()

        # Send the reset email
        msg = Message('Password Reset Request', sender='your_email@example.com', recipients=[email])
        msg.body = f"Please click the following link to reset your password: {url_for('student_api.resetPasswordConfirm', token=token, _external=True)}"
        mail.send(msg)
        flash('An email with instructions to reset your password has been sent.', 'info')
        return jsonify({'success': True, 'message': 'An email with instructions to reset your password has been sent to email.'}),200
    else:
        return jsonify({'error': True, 'message': 'Email is invalid'}), 400


# Step 6: Create a route to render the password reset confirmation form
@student_api.route('/reset_password_confirm/<token>', methods=['GET'])
@preventAuthenticated
def resetPasswordConfirm(token):
    # Check if the token is valid and not expired
    student = Student.query.filter_by(Token=token).first()
    if student and student.TokenExpiration > datetime.now():
        return render_template('student/reset_password_confirm.html', token=token, student_api_base_url=student_api_base_url)
    else:
        flash('Invalid or expired token.', 'danger')
        return render_template('404.html')
# student_api.py (continued)


# Step 8: Handle the form submission for resetting the password
@student_api.route('/reset_password_confirm/<token>', methods=['POST'])
def resetPassword(token):
    data = request.get_json()
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    # Check new password if length is 8
    if len(new_password) < 8:
        return jsonify({'message': 'New Password must be at least 8 characters', 'status': 400})
    
    if len(confirm_password) < 8:
        return jsonify({'message': 'Confirm Password must be at least 8 characters', 'status': 400})
    
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$', new_password):
        return jsonify({'message': 'New Password must contain uppercase, lowercase characters and number', 'status': 400})
    
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$', confirm_password):
        return jsonify({'message': 'New Password must contain uppercase, lowercase characters and number', 'status': 400})
    
    if new_password != confirm_password:
        return jsonify({'message': 'Passwords do not match', 'status': 400})
    else: 
        # Check if the token is valid and not expired
        student = Student.query.filter_by(Token=token).first()

        if student and student.TokenExpiration > datetime.now():
            # Update the password for the user in the database
            student.Password = generate_password_hash(new_password)

            # Clear the token and expiration
            student.Token = None
            student.TokenExpiration = None

            db.session.commit()

            return jsonify({'message': 'Password reset successfully', 'status': 200})
        else:
            return jsonify({'message': 'Invalid or expired token', 'status': 400})


# # ===================================================
# # Required params (#auth headers, username, password, grant_type, scope)
# @student_api.route('/oauth/token', methods=['POST'])
# def login():
#     # Get the params sessionVal in link
#     saveSession = request.args.get('saveSession')
    
#     data = request.form.to_dict()
#     email = data.get('username')
#     password = data.get('password')
    
#     print("Email: ", email)
#     print("Password: ", password)
    
#     # Check the student
#     user = Student.query.filter_by(Email=email).first()
    
#     # Check if password is match
#     if user and check_password_hash(user.Password, password):
#         print("INSIDE")
#         # save user_id in session
        
#         # Check if studentId already have OAuth Token
#         existing_token = OAuth2Token.query.filter_by(user_id=user.StudentId).first()
#         print("EXIST")
        
#         if existing_token:
#             # Check if issued_at already reach the expires_in
#             if existing_token.issued_at + existing_token.expires_in < time.time():
#                 # Update access token and issued at
#                 existing_token.access_token = gen_salt(40)
#                 existing_token.issued_at = time.time()
#                 # Update the access_token_revoked_at in current time with additional 15 mins
#                 print('existing_token.access_token_revoked_at: ', existing_token.access_token_revoked_at)
#                 existing_token.access_token_revoked_at = time.time() + (15 * 60)
#                 existing_token.refresh_token_revoked_at = time.time() + (24 * 60 * 60)

#                 print("NEW REVOKE")
#                 # Commit to the database
#                 token = existing_token.to_token_response()
#                 db.session.commit()
                
#                 if saveSession == "True":
#                     saveSessionValues(user.StudentId, token)
                
#                 return jsonify(token)
#             else:
#                 # Update the existing access token and return it
#                 existing_token.access_token = gen_salt(40)
#                 existing_token.access_token_revoked_at = time.time() + (15 * 60)
#                 existing_token.refresh_token_revoked_at = time.time() + (24 * 60 * 60)

#                 # Commit to the database
#                 token = existing_token.to_token_response()
#                 db.session.commit()
                
#                 if saveSession == "True":
#                     saveSessionValues(user.StudentId, token)
                    
#                 return jsonify(token)
#         else:
#             token = authorization.create_token_response()
#             tokenval = token.json
#             token_resp = OAuth2Token.query.filter_by(access_token=tokenval['access_token'], refresh_token=tokenval['refresh_token']).first()
#             dict_token_resp = token_resp.to_token_response()
            
#             if saveSession == "True":
#                 saveSessionValues(user.StudentId, dict_token_resp)
            
#             return dict_token_resp
#         # return redirect('/')
#     else:
#         return jsonify({'error': 'Invalid username or password'}), 401

# # Make a token validator that will check whether the access token is correct
# # Required parms (user_id, access_token)
# @student_api.route('/oauth/validate', methods=['POST'])
# def validateToken():
#     access_token = request.args.get('access_token')
#     user_id = request.args.get('user_id')

#     print('acess_token: ', access_token)
#     # Check the token
#     token = OAuth2Token.query.filter_by(access_token=access_token, user_id=user_id).first()
#     if token:
#         # Token expiration check must implemented if the access_token has a value
        
#         return jsonify({ 'success': True, 'error': False,  'message': 'Token is valid' }), 200
#     else:
#         return jsonify({ 'success': False, 'error': True, 'message': 'Invalid token' }), 401


# # Make a token refresh that will refresh token
# # Required parms (user_id, refresh_token)
# @student_api.route('/oauth/refresh', methods=['POST'])
# def refreshToken():
#     refresh_token = request.args.get('refresh_token')
#     user_id = request.args.get('user_id')

#     # Check the token
#     token = OAuth2Token.query.filter_by(refresh_token=refresh_token, user_id=user_id).first()
#     if token:
#         # Check if issued at reach the time already
#         if token.issued_at + token.expires_in < time.time():
#             # Return refresh token is already expired. Please login again
#             return jsonify({ 'success': False, 'error': True, 'message': 'Refresh token is already expired. Please login again' }), 401
#         else:
#             token.access_token = gen_salt(40)
#             # Commit to the database
#             db.session.commit()
#             return jsonify(token.to_token_response())
#     else:
#         return jsonify({ 'success': False, 'error': True, 'message': 'Invalid token' }), 401


# Make a token validator that will check whether the access token is correct
# Required parms (user_id, access_token)
@student_api.route('/oauth/validate', methods=['POST'])
def validateToken():
    access_token = request.args.get('access_token')
    user_id = request.args.get('user_id')

    print('acess_token: ', access_token)
    # Check the token
    token = OAuth2Token.query.filter_by(access_token=access_token, user_id=user_id).first()
    if token:
        # Token expiration check must implemented if the access_token has a value
        
        return jsonify({ 'success': True, 'error': False,  'message': 'Token is valid' }), 200
    else:
        return jsonify({ 'success': False, 'error': True, 'message': 'Invalid token' }), 401


# Make a token refresh that will refresh token
# Required parms (user_id, refresh_token)
@student_api.route('/oauth/refresh', methods=['POST'])
def refreshToken():
    refresh_token = request.args.get('refresh_token')
    user_id = request.args.get('user_id')

    # Check the token
    token = OAuth2Token.query.filter_by(refresh_token=refresh_token, user_id=user_id).first()
    if token:
        # Check if issued at reach the time already
        if token.issued_at + token.expires_in < time.time():
            # Return refresh token is already expired. Please login again
            return jsonify({ 'success': False, 'error': True, 'message': 'Refresh token is already expired. Please login again' }), 401
        else:
            token.access_token = gen_salt(40)
            # Commit to the database
            db.session.commit()
            return jsonify(token.to_token_response())
    else:
        return jsonify({ 'success': False, 'error': True, 'message': 'Invalid token' }), 401

# # Student User Log in
# @student_api.route('/login', methods=['POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         # create_app.sayHello()
#         student = Student.query.filter_by(Email=email).first()
#         if student and check_password_hash(student.Password, password):
#             # Successfully authenticated
#             # access_token = create_access_token(identity=student.StudentId)
#             # refresh_token = create_refresh_token(identity=student.StudentId)
#             session['user_id'] = student.StudentId
#             session['user_role'] = 'student'
            
#             # session['student_id'] = student.StudentId
#             return jsonify({"message": "Login successful"}), 200
#         else:
#             return jsonify({"message": "Invalid email or password"}), 401
#     return jsonify({"message": "Method not allowed"}), 405



@student_api.route('/profile')
@require_oauth('student')
def profile():
    # print('current_token: ', current_token)
    student = getCurrentUser()
    if student:
        return jsonify(student.to_dict())
    else:
        flash('User not found', 'danger')
        return redirect(url_for('student_api.login'))
    # Check the token
    # user = current_token.user
    # return jsonify(id=user.StudentId, username=user.Name)

    # Return hello
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
    
    
@student_api.route('/units', methods=['GET'])
@role_required('student')
def fetchUnitsTaken():
    student = getCurrentUser()
    if student:
        json_overall_gpa = getUnitsTaken(student.StudentId)

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
        dict_student = student.to_dict()  # Assuming to_dict() returns a dictionary
        print('dict_student: ', dict_student['StudentId'])

        # Find course enrolled
        data_course_enrolled = (
            db.session.query(CourseEnrolled, Course)
            .join(Course, Course.CourseId == CourseEnrolled.CourseId)
            .filter(CourseEnrolled.StudentId == dict_student['StudentId'])
            .order_by(desc(CourseEnrolled.created_at))
            .first()
        )
        
        dict_student['CourseName'] = data_course_enrolled.Course.Name
        
        # print('data_course_enrolled: ', data_course_enrolled)
        # return student to_dict
        return jsonify(dict_student)
    else:
        return render_template('404.html'), 404


# Updating the user details
@student_api.route('/details/update', methods=['POST'])
@role_required('student')
def updateDetails():
    student = getCurrentUser()
    if student:
        if request.method == 'POST':
            number = request.json.get('number')
            residentialAddress = request.json.get('residentialAddress')

            json_result = updateStudentData(
                student.StudentId, number, residentialAddress)

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
            return jsonify(error="No data available")
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
            return ({'success': True, 'data':json_previous_grade})
        else:
            return jsonify({'error': True, 'message':'No Grades data available'})
    else:
        return render_template('404.html'), 404

# Current Course Performance
@student_api.route('/course-performance', methods=['GET'])
@role_required('student')
def coursePerformance():
    student = getCurrentUser()
    if student:
        json_course_performance = getCoursePerformance()

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
            return jsonify(error="No data available")
    else:
        return render_template('404.html'), 404
