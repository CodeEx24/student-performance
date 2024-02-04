# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import Registrar

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required
from decorators.rate_decorators import login_decorator, resend_otp_decorator

# FUNCTIONS IMPORT
from .utils import getCurrentUser, getUniversityAdminData, updatePassword, getStatistics, getEnrollmentTrends, getOverallCoursePerformance, getStudentData, processAddingStudents, deleteStudentData, getStudentAddOptions, updateRegistrarData, getStudentRequirements, processUpdatingStudentRequirements
import os


registrar_api = Blueprint('registrar_api', __name__)

@registrar_api.route('/login', methods=['POST'])
# @login_decorator("Too many login attempts. Please try again later")
def login():
    try:
        print("HERE IN REGISTRAR LOGIN")
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            registrar = Registrar.query.filter_by(Email=email).first()
            if registrar and check_password_hash(registrar.Password, password):
                session['user_id'] = registrar.RegistrarId
                session['user_role'] = 'registrar'
                return jsonify({"success": True, "message": "Login successful"}), 200
            else:
                # Return
                return jsonify({"error": True, "message": "Invalid email or password"}), 401
            # return redirect('/')
        else:
            return jsonify({'error': True, 'message': 'Invalid username or password'}), 401
    except Exception as e:
      return jsonify({'error': True, 'message': 'Something went wrong'})
  
# ===================================================
# TESTING AREA
@registrar_api.route('/profile', methods=['GET'])
@role_required('registrar')
def profile():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        return jsonify(universityAdmin.to_dict())
    else:
        flash('User not found', 'danger')
        return redirect(url_for('university_admin_api.login'))

# ===================================================

# Getting the user details
@registrar_api.route('/', methods=['GET'])
@role_required('registrar')
def registrarData():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_university_admin_data = getUniversityAdminData(universityAdmin.UnivAdminId)
        if json_university_admin_data:
            return (json_university_admin_data)
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
@registrar_api.route('/enrollment/trends', methods=['GET'])
@role_required('registrar')
def enrollmentTrends():
    registrar = getCurrentUser()
    if registrar:
        json_performance_data = getEnrollmentTrends()

        if json_performance_data:
            return (json_performance_data)
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
        print('result: ', result)
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
