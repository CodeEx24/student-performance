# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import Faculty, db
import secrets
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required, preventAuthenticated
from decorators.rate_decorators import login_decorator, resend_otp_decorator
from werkzeug.security import generate_password_hash
from flask_mail import Message
from mail import mail  # Import mail from the mail.py module
from .utils import getSubjectCount, getHighLowAverageClass, getAllClassAverageWithPreviousYear, getPassFailRates, getTopPerformerStudent, getStudentClassSubjectGrade, getAllClass, getClassPerformance, updateFacultyData, getFacultyData, updatePassword, getStudentPerformance, getCurrentUser, processGradeSubmission, processGradePDFSubmission
import re
import os

faculty_api_base_url = os.getenv("FACULTY_API_BASE_URL")
faculty_api = Blueprint('faculty_api', __name__)

# Api/v1/faculty/api_routes.py
# Define a function to get the current faculty


@faculty_api.route('/login', methods=['POST'])
# @login_decorator("Too many login attempts. Please try again later")
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            
            if not email or not password:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401

            # if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
            #     return jsonify({'error': True, 'message': 'Invalid email format type'}), 401
            
            teacher = Faculty.query.filter_by(Email=email).first()
            if not teacher:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401
            
            if teacher and check_password_hash(teacher.Password, password):
                session['user_id'] = teacher.FacultyId
                session['user_role'] = 'faculty'
                return jsonify({"success": True, "message": "Login successful"}), 200
            else:
                return jsonify({"error": True, "message": "Invalid email or password"}), 401
        except Exception as e:
            print('An exception occurred')
            return jsonify({"error": True, "message": "Invalid email or password"}), 401



# Step 4: Handle the form submission for requesting a password reset email
@faculty_api.route('/reset_password', methods=['POST'])
def forgotPassword():
    data = request.get_json()
    email = data.get('email')

    # Check if email exists in the database
    faculty = Faculty.query.filter_by(Email=email).first()

    if faculty:
        # Generate a secure token
        token = secrets.token_hex(16)

        # Save the token and its expiration time in the database
        faculty.Token = token
        faculty.TokenExpiration = datetime.now() + timedelta(minutes=30)
        db.session.commit()

        # Send the reset email
        msg = Message('Password Reset Request', sender='your_email@example.com', recipients=[email])
        msg.body = f"Please click the following link to reset your password: {url_for('faculty_api.resetPasswordConfirm', token=token, _external=True)}"
        mail.send(msg)
        flash('An email with instructions to reset your password has been sent.', 'info')
        return jsonify({'message': 'An email with instructions to reset your password has been sent to email.'}),200
    else:
        return jsonify({'message': 'Invalid email'}), 400



# Step 6: Create a route to render the password reset confirmation form
@faculty_api.route('/reset_password_confirm/<token>', methods=['GET'])
@preventAuthenticated
def resetPasswordConfirm(token):
    # Check if the token is valid and not expired
    student = Faculty.query.filter_by(Token=token).first()
    if student and student.TokenExpiration > datetime.now():
        return render_template('student/reset_password_confirm.html', token=token, faculty_api_base_url=faculty_api_base_url)
    else:
        flash('Invalid or expired token.', 'danger')
        return render_template('404.html')
# student_api.py (continued)


# Step 8: Handle the form submission for resetting the password
@faculty_api.route('/reset_password_confirm/<token>', methods=['POST'])
def resetPassword(token):
    data = request.get_json()
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if new_password != confirm_password:
        return jsonify({'message': 'Passwords do not match', 'status': 400})
    else: 
        # Check if the token is valid and not expired
        student = Faculty.query.filter_by(Token=token).first()

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
        json_faculty_data = getFacultyData(faculty.FacultyId)
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
            # email = request.json.get('email')
            number = request.json.get('number')
            residential_address = request.json.get('residential_address')

            json_result = updateFacultyData(
                faculty.FacultyId, number, residential_address)

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

            json_result = updatePassword(faculty.FacultyId, password, new_password, confirm_password)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('facultyLogin'))
    else:
        return render_template('404.html'), 404


# Getting the Highest and Lowest Class Average
@faculty_api.route('/class-statistics', methods=['GET'])
@role_required('faculty')
def classAverageAndSubjectCount():
    faculty = getCurrentUser()
    if faculty:
        json_high_low_class = getHighLowAverageClass(faculty.FacultyId)
        json_subject_count = getSubjectCount(faculty.FacultyId)
        if json_high_low_class and json_subject_count is not None:
            return ({**json_high_low_class, **json_subject_count})
        else:
            return jsonify(error="Something went wrong")
    else:
        return render_template('404.html'), 404


# All class average per year
@faculty_api.route('/class-average', methods=['GET'])
@role_required('faculty')
def allClassAverages():
    faculty = getCurrentUser()
    if faculty:
        json_average_class = getAllClassAverageWithPreviousYear(faculty.FacultyId)

        if json_average_class:
            return (json_average_class)
        else:
            return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Get the pass and failed counts to the facultys subject
@faculty_api.route('/pass-fail', methods=['GET'])
@role_required('faculty')
def passFailRates():
    faculty = getCurrentUser()
    if faculty:
        json_average_class = getPassFailRates(faculty.FacultyId)

        if json_average_class:
            return (json_average_class)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the top performer student
@faculty_api.route('/top-student/', methods=['GET'])
@role_required('faculty')
def topPerformerStudent():
    faculty = getCurrentUser()
    if faculty:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_top_performer_student = getTopPerformerStudent(skip, top, order_by, filter)

        if json_top_performer_student:
            return (json_top_performer_student)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the student subject grade in a class
@faculty_api.route('/class-subject-grade/', methods=['GET'])
@role_required('faculty')
def studentClassSubjectGrade():
    faculty = getCurrentUser()
    
    if faculty:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
      
        # json_class_subject_grade = getStudentClassSubjectGrade(
        #     faculty.FacultyId)
        json_class_subject_grade = getStudentClassSubjectGrade(
            faculty.FacultyId, skip, top, order_by, filter)

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
            faculty.FacultyId)

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

# api_routes.py
@faculty_api.route('/submit-grades', methods=['POST'])
@role_required('faculty')
def submitGrades():
    # Check if the request contains a file named 'excelFile'
    if 'pdf-file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['pdf-file']

    return processGradePDFSubmission(file)


    # # Check if the request contains a file named 'excelFile'
    # if 'pdf-file' not in request.files:
    #     return jsonify({'error': 'No file part'}), 400

    # file = request.files['pdf-file']
    # print('PDF FILE: ', file)
    # header_names = ['StudentNumber', 'Grade', 'SubjectCode', 'Year', 'Semester', 'Batch']
    # grade = processGradePDFSubmission(file, header_names)
    # print(grade)
    # return grade

    # Call the utility function to process the file
    # return processGradeSubmission(file)


    # You can also perform additional processing on the uploaded file here.

    # return jsonify({'success': 'File uploaded and processed successfully'}), 200
    
    # faculty = getCurrentUser()
    # if faculty:
    #     json_student_performance = getStudentPerformance(id)

    #     if json_student_performance:
    #         return (json_student_performance)
    #     else:
    #         return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    # else:
    #     return render_template('404.html'), 404
