# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import Registrar

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required
from decorators.rate_decorators import login_decorator, resend_otp_decorator

# FUNCTIONS IMPORT
from .utils import getCurrentUser, getRegistrarData, updatePassword, getStatistics, getEnrollmentTrends, getOverallCoursePerformance, getStudentData, processAddingStudents, deleteStudentData, getStudentAddOptions, updateRegistrarData, getStudentRequirements, processUpdatingStudentRequirements, getListerTrends, processUpdatingSingleStudentRequirements, noticeStudentsEmail, getOutcomeRates, getBatchLatest, getGradDropWithdrawnRate, getPassFailedAndDropout, getAllCourses
import os
import re

registrar_api = Blueprint('registrar_api', __name__)

@registrar_api.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        try:
            print("DONE 1")
            email = request.form['email']
            password = request.form['password']
            print("DONE 2")
            if not email or not password:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401
            print("DONE 3")
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
                return jsonify({'error': True, 'message': 'Invalid email format type'}), 401
            print("DONE 4")
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