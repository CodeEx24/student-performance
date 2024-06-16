# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import Registrar, db

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required

# FUNCTIONS IMPORT
from .utils import getCurrentUser, getRegistrarData, updatePassword, getStatistics, getEnrollmentTrends, getOverallCoursePerformance, getStudentData, processAddingStudents, deleteStudentData, getStudentAddOptions, updateRegistrarData, getStudentRequirements, processUpdatingStudentRequirements, getListerTrends, processUpdatingSingleStudentRequirements, noticeStudentsEmail, getOutcomeRates, getBatchLatest, getGradDropWithdrawnRate, getPassFailedAndDropout, getAllCourses

from datetime import datetime, timedelta
from decorators.auth_decorators import preventAuthenticated, role_required
from werkzeug.security import generate_password_hash
from flask_mail import Message
from mail import mail  # Import mail from the mail.py module

import os
import re
import secrets


registrar_api_base_url = os.getenv("REGISTRAR_API_BASE_URL")
registrar_api = Blueprint('registrar_api', __name__)

@registrar_api.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        try:
            print("DONE 1")
            email = request.form['email']
            password = request.form['password']
            print("DONE 2: ", password)
            if not email or not password:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401
            print("DONE 3")
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
                return jsonify({'error': True, 'message': 'Invalid email format type'}), 401
            print("DONE 4")
            print("EMAIL: ", email)
            registrar = Registrar.query.filter_by(Email=email).first()
            if not registrar:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401
            print("DONE 5")
            if registrar and check_password_hash(registrar.Password, password):
                print("DONE 6")
                session['user_id'] = registrar.RegistrarId
                session['user_role'] = 'registrar'
                return jsonify({"success": True, "message": "Login successful"})
            else:
                print("DONE 7")
                # Return
                return jsonify({"error": True, "message": "Invalid email or password"}), 401
        # return redirect('/')
        except Exception as e:
            print("Except into error: ", e)
            return jsonify({'error': True, 'message': 'Invalid email or password'})
  
       
# Step 4: Handle the form submission for requesting a password reset email
@registrar_api.route('/reset_password', methods=['POST'])
def forgotPassword():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': True, 'message': 'Please input an email'}), 401

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
        return jsonify({'error': True, 'message': 'Invalid email format type'}), 401
    
    # Check if email exists in the database
    registrar = Registrar.query.filter_by(Email=email).first()

    if not registrar:
        # Intended so the intruder cannot be able to know whether email is registered or not
        return jsonify({'success': True, 'message': 'An email with instructions to reset your password has been sent to email.'}),200
        # return jsonify({'error': True, 'message': 'Email is invalid'}), 400

    if registrar:
        # Generate a secure token
        token = secrets.token_hex(16)

        # Save the token and its expiration time in the database
        registrar.Token = token
        registrar.TokenExpiration = datetime.now() + timedelta(minutes=30)
        db.session.commit()

        # Send the reset email
        msg = Message('Password Reset Request', sender='your_email@example.com', recipients=[email])
        msg.body = f"Please click the following link to reset your password: {url_for('registrar_api.resetPasswordConfirm', token=token, _external=True)}"
        mail.send(msg)
        flash('An email with instructions to reset your password has been sent.', 'info')
        return jsonify({'success': True, 'message': 'An email with instructions to reset your password has been sent to email.'}),200
    else:
        return jsonify({'error': True, 'message': 'Email is invalid'}), 400


# Step 6: Create a route to render the password reset confirmation form
@registrar_api.route('/reset_password_confirm/<token>', methods=['GET'])
@preventAuthenticated
def resetPasswordConfirm(token):
    # Check if the token is valid and not expired
    registrar = Registrar.query.filter_by(Token=token).first()
    if registrar and registrar.TokenExpiration > datetime.now():
        return render_template('registrar/reset_password_confirm.html', token=token, registrar_api_base_url=registrar_api_base_url)
    else:
        flash('Invalid or expired token.', 'danger')
        return render_template('404.html')
# registrar_api.py (continued)


# Step 8: Handle the form submission for resetting the password
@registrar_api.route('/reset_password_confirm/<token>', methods=['POST'])
def resetPassword(token):
    data = request.get_json()
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    print("BY PASS")
    # Check new password if length is 8
    if len(new_password) < 8:
        return jsonify({'message': 'New Password must be at least 8 characters', 'status': 400})
    
    if len(confirm_password) < 8:
        return jsonify({'message': 'Confirm Password must be at least 8 characters', 'status': 400})
    
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$', new_password):
        return jsonify({'message': 'New Password must contain uppercase, lowercase characters and number', 'status': 400})
    
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$', confirm_password):
        return jsonify({'message': 'New Password must contain uppercase, lowercase characters and number', 'status': 400})
    print("BY PASS2")
    if new_password != confirm_password:
        return jsonify({'message': 'Passwords do not match', 'status': 400})
    else: 
        # Check if the token is valid and not expired
        registrar = Registrar.query.filter_by(Token=token).first()
        print("registrar: ", registrar)
        if registrar and registrar.TokenExpiration > datetime.now():
            # Update the password for the user in the database
            registrar.Password = generate_password_hash(new_password)

            # Clear the token and expiration
            registrar.Token = None
            registrar.TokenExpiration = None

            db.session.commit()

            return jsonify({'message': 'Password reset successfully', 'success': True, 'status': 200})
        else:
            return jsonify({'message': 'Invalid or expired token', 'status': 400})
       
       
    
# ===================================================
# TESTING AREA
@registrar_api.route('/profile', methods=['GET'])
@role_required('registrar')
def profile():
    registrar = getCurrentUser()
    if registrar:
        return jsonify(registrar.to_dict())
    else:
        flash('User not found', 'danger')
        return redirect(url_for('university_admin_api.login'))

# ===================================================

# Getting the user details
@registrar_api.route('/', methods=['GET'])
@role_required('registrar')
def registrarData():
    registrar = getCurrentUser()
    if registrar:
        json_registrar_data = getRegistrarData(registrar.RegistrarId)
        if json_registrar_data:
            return (json_registrar_data)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404


@registrar_api.route('/statistics', methods=['GET'])
@role_required('registrar')
def fetchStatistics():
    registrar = getCurrentUser()
    if registrar:
        class_list = getStatistics()
        # return class list
        if class_list:
            return (class_list)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    

# Getting the enrollment trends of different courses
@registrar_api.route('/enrollment/trends/<int:startYear>/<int:endYear>', methods=['GET'])
@role_required('registrar')
def enrollmentTrends(startYear, endYear):
    registrar = getCurrentUser()
    if registrar:
        json_performance_data = getEnrollmentTrends(startYear, endYear)

        if json_performance_data:
            return (json_performance_data)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404
    

@registrar_api.route('/outcome/rates/<int:semester>', methods=['GET'])
@role_required('registrar')
def fetchOutcomeRates(semester):
    registrar = getCurrentUser()
    if registrar:
        json_outcome_data = getOutcomeRates(semester)

        if json_outcome_data:
            return (json_outcome_data)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404


# Getting the overall course performance
@registrar_api.route('/overall/course/performance', methods=['GET'])
@role_required('registrar')
def overallCoursePerformance():
    registrar = getCurrentUser()
    if registrar:
        json_performance_data = getOverallCoursePerformance()

        if json_performance_data:
            return  json_performance_data
        else:
            return jsonify(error="No Performance data available")
    else:
        return render_template('404.html'), 404
    

# Getting the enrollment trends of different courses
@registrar_api.route('/lister/trends', methods=['GET'])
@role_required('registrar')
def listerTrends():
    registrar = getCurrentUser()
    if registrar:
        json_lister_data = getListerTrends()

        if json_lister_data:
            return (json_lister_data)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404
    

# api_routes.py
@registrar_api.route('/students/', methods=['GET'])
@role_required('registrar')
def fetchStudents():
    registrar = getCurrentUser()
    if registrar:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_student_data = getStudentData(skip, top, order_by, filter)

        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
    

@registrar_api.route('/students/insert', methods=['POST'])
@role_required('registrar')
def insertStudent():
    registrar = getCurrentUser()
    if registrar:
        data = request.json  # assuming the data is sent as JSON
        result = processAddingStudents(data)
        print('result: ', result)
        return result
    else:
        return render_template('404.html'), 404
    

@registrar_api.route('/students/delete(<int:studentId>)', methods=['DELETE'])
@role_required('registrar')
def deleteStudent(studentId):
    registrar = getCurrentUser()
    if registrar:
        result = deleteStudentData(studentId)
        return result
    else:
        return render_template('404.html'), 404
    

# api_routes.py
@registrar_api.route('/student/options', methods=['GET'])
@role_required('registrar')
def fetchStudentDataOptions():
    registrar = getCurrentUser()
    if registrar:
        json_student_data_options = getStudentAddOptions()

        if json_student_data_options:
            return (json_student_data_options)
        else:
            return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
    
    
# Updating the user details
@registrar_api.route('/details/update', methods=['POST'])
@role_required('registrar')
def updateDetails():
    registrar = getCurrentUser()
    if registrar:
        if request.method == 'POST':
            number = request.form.get('number')
            residential_address = request.form.get('residential-address')
          
            json_result = updateRegistrarData(registrar.RegistrarId, number, residential_address)
            return json_result
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
        
        
# Changing the password of the user
@registrar_api.route('/change/password', methods=['POST'])
@role_required('registrar')
def changePassword():
    registrar = getCurrentUser()
    if registrar:
        if request.method == 'POST':
            password = request.json.get('password')
            new_password = request.json.get('new_password')
            confirm_password = request.json.get('confirm_password')

            json_result = updatePassword(
                registrar.RegistrarId, password, new_password, confirm_password)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404
    

# api_routes.py
@registrar_api.route('/submit-students', methods=['POST'])
@role_required('registrar')
def submitStudents():
    registrar = getCurrentUser()
    if registrar:
            # Check if the request contains a file named 'excelFile'
        if 'excelFile' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['excelFile']

        # Call the utility function to process the file
        return processAddingStudents(file, excelType=True)
    else:
        return render_template('404.html'), 404
   

# api_routes.py
@registrar_api.route('/student/requirements/', methods=['GET'])
@role_required('registrar')
def studentRequirements():
    registrar = getCurrentUser()
    if registrar:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_student_data = getStudentRequirements(skip, top, order_by, filter)

        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404

# api_routes.py
@registrar_api.route('/submit/student-requirements', methods=['POST'])
@role_required('registrar')
def submitStudentsRequirements():
    # Check if the request contains a file named 'excelFile'
    if 'excelFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['excelFile']

    # Call the utility function to process the file
    return processUpdatingStudentRequirements(file)

@registrar_api.route('/submit/student-requirements/<int:studentId>', methods=['POST'])
@role_required('registrar')
def submitSingleStudentsRequirements(studentId):
    registrar = getCurrentUser()
    if registrar:
        data = request.form
        
        object_data = {}
        # loop the data item
        for key, value in data.items():
            object_data[key] = True if value == 'on' else False

        return processUpdatingSingleStudentRequirements(studentId, object_data)
    else:
        return render_template('404.html'), 404


@registrar_api.route('/notice/students', methods=['POST'])
@role_required('registrar')
def noticeStudents():
    registrar = getCurrentUser()
    if registrar:
        result = noticeStudentsEmail()
        return result
    else:
        return render_template('404.html'), 404
    
    
@registrar_api.route('/batch/latest', methods=['GET'])
@role_required('registrar')
def fetchBatchLatest():
    registrar = getCurrentUser()
    if registrar:
        return getBatchLatest()
    else:
        return render_template('404.html'), 404   
    
@registrar_api.route('/grad-drop-withdrawn/rates/<int:year>', methods=['GET'])
@role_required('registrar')
def fetchGraduateDropWithdrawnRates(year):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        return getGradDropWithdrawnRate(year)
    else:
        return render_template('404.html'), 404    
        
    

@registrar_api.route('/passing-drop-withdrawn-and-failed/<int:programId>/<int:startingYear>/<int:endingYear>', methods=['GET'])
@role_required('registrar')
def fetchPassFailedAndDropout(programId, startingYear, endingYear):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        return getPassFailedAndDropout(programId, startingYear, endingYear)
    else:
        return render_template('404.html'), 404    
    

@registrar_api.route('/courses', methods=['GET'])
@role_required('registrar')
def fetchAllCourses():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_courses = getAllCourses()
        if json_courses:
            return  json_courses
        else:
            return jsonify(error="No Performance data available")
    else:
        return render_template('404.html'), 404