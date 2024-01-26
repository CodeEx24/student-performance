# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import SystemAdmin, OAuth2Client, db, Student, OAuth2Token
from authlib.oauth2 import OAuth2Error

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required
import time
from werkzeug.security import gen_salt
from oauth2 import authorization

from .utils import getCurrentUser, getClientList, getClientsData, getAllClassData, getBatchSemester, getStudentData, getFacultyData, updateStudentData, getStudentAddOptions, revertFinalizedGrades, updateSystemAdminData
from decorators.rate_decorators import login_decorator, resend_otp_decorator

import os

system_admin_api = Blueprint('system_admin_api', __name__)


def current_user():
    if 'id' in session:
        uid = session['id']
        return SystemAdmin.query.get(uid)
    return None

# Login
@system_admin_api.route('/login', methods=['POST'])
# @login_decorator("Too many login attempts. Please try again later")
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(email)
        user = SystemAdmin.query.filter_by(Email=email).first()
        print('user: ', user)
        # Check for password
        if user and check_password_hash(user.Password, password):
            session['user_id'] = user.SysAdminId
            print("LOGIN : ", user.SysAdminId)
            session['user_role'] = 'systemAdmin'
            user = current_user()
            return jsonify({"success": True, "message": "Login successful"}), 200
        else:
            # Return
            return jsonify({"error": True, "message": "Invalid email or password"}), 401
        # return redirect('/')
    else:
        return jsonify({'error': True, 'message': 'Invalid username or password'}), 401


# Make a client list route
@system_admin_api.route('/clients/', methods=['GET'])
def clients():
    user = getCurrentUser()
    if user:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
      
        json_class_subject_grade = getClientList(skip, top, order_by, filter)

        if json_class_subject_grade:
            return (json_class_subject_grade)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return jsonify({"message": "No clients found"}), 404
    
    

@system_admin_api.route('/create_client', methods=['POST'])
def createClient():
    systemAdmin = current_user()
    print('form: ', form)
    if request.method == "POST":
        if not systemAdmin:
            return redirect(url_for('systemAdminLogin'))
        
        client_id = gen_salt(24)
        client_id_issued_at = int(time.time())
        client = OAuth2Client(
            client_id=client_id,
            client_id_issued_at=client_id_issued_at,
            user_id=systemAdmin.SysAdminId,
        )

        form = request.form
        client_metadata = {
            "client_name": form["client_name"],
            "client_uri": form["client_uri"],
            "grant_types": split_by_crlf(form["grant_type"]),
            "redirect_uris": split_by_crlf(form["redirect_uri"]),
            "response_types": split_by_crlf(form["response_type"]),
            "scope": form["scope"],
            "token_endpoint_auth_method": form["token_endpoint_auth_method"]
        }
        client.set_client_metadata(client_metadata)

        if form['token_endpoint_auth_method'] == 'none':
            client.client_secret = ''
        else:
            client.client_secret = gen_salt(48)

        db.session.add(client)
        db.session.commit()
        return redirect(url_for('systemAdminClients'))
        
    
# Updating the user details
@system_admin_api.route('/details/update', methods=['POST'])
@role_required('systemAdmin')
def updateDetails():
    print("HERE IN DETAILS UPDATE")
    systemAdmin = getCurrentUser()
    if systemAdmin:
        if request.method == 'POST':
            number = request.form.get('number')
            residential_address = request.form.get('residential-address')
            print('NUMBER: ', number)
            print('residential_address: ', residential_address)
            json_result = updateSystemAdminData(systemAdmin.SysAdminId, number, residential_address)
            return json_result
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))  

# Create token checker
    
@system_admin_api.route('/login2', methods=['POST'])
def login2():
    print("CHECKING SYSTEM LOGIN")
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print("CHECKING SYSTEM LOGIN")
        systemAdmin = SystemAdmin.query.filter_by(Email=email).first()
        if systemAdmin and check_password_hash(systemAdmin.Password, password):
            session['user_id'] = systemAdmin.SysAdminId
            session['user_role'] = 'systemAdmin'
            print("SUCCESSFUL LOGIN")
            return redirect(url_for('systemAdminHome'))
        else:
            flash('Invalid email or password', 'danger')
            print("FAILED LOGIN")
            return redirect(url_for('systemAdminLogin'))
    return redirect(url_for('systemAdminLogin'))


@system_admin_api.route('/ads', methods=['GET'])
def helo():
    print("CHECKING SYSTEM LOGIN")
    return ({"message": " HELLO THERE FROM RTHIS"})

    
# Getting all the class data in current year
@system_admin_api.route('/class/', methods=['GET'])
@role_required('systemAdmin')
def classData():
    systemAdmin = getCurrentUser()
    print('systemAdmin: ', systemAdmin)
    if systemAdmin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_class_data = getAllClassData(skip, top, order_by, filter)

        if json_class_data:
            return (json_class_data)
        else:
            return jsonify(message="No Class data available")
    else:
        return render_template('404.html'), 404


@system_admin_api.route('/client/<int:Id>', methods=['GET'])
@role_required('systemAdmin')
def clientData(Id):
    systemAdmin = getCurrentUser()
    if systemAdmin:
        json_class_subject_grade = getClientsData(Id)
 
        if json_class_subject_grade:
            return (json_class_subject_grade)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return jsonify({"message": "No clients found"}), 404
    

# api_routes.py
@system_admin_api.route('/finalized/batch/', methods=['GET'])
@role_required('systemAdmin')
def fetchBatchSemester():
    systemAdmin = getCurrentUser()
    if systemAdmin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_student_data = getBatchSemester(skip, top, order_by, filter)

        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
    
    
# api_routes.py
@system_admin_api.route('/students/', methods=['GET'])
@role_required('systemAdmin')
def fetchStudents():
    systemAdmin = getCurrentUser()
    if systemAdmin:
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
    
@system_admin_api.route('/faculty/', methods=['GET'])
@role_required('systemAdmin')
def fetchFaculty():
    systemAdmin = getCurrentUser()
    if systemAdmin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_faculty_data = getFacultyData(skip, top, order_by, filter)

        if json_faculty_data:
            return (json_faculty_data)
        else:
            return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
    
    # Check if token
    # token = authorization.create_token_response()
    # print(token)
    # return token


@system_admin_api.route('/students/update(<int:studentId>)', methods=['PUT'])
@role_required('systemAdmin')
def deleteStudent(studentId):
    university_admin = getCurrentUser()
    if university_admin:
        updated_data = request.json

        
        result = updateStudentData(studentId, updated_data)
        print('result: ', result)
        return result
    else:
        return render_template('404.html'), 404


# api_routes.py
@system_admin_api.route('/student/options', methods=['GET'])
@role_required('systemAdmin')
def fetchStudentDataOptions():
    university_admin = getCurrentUser()
    if university_admin:
        
        json_student_data_options = getStudentAddOptions()

        if json_student_data_options:
            return json_student_data_options
        else:
            return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


@system_admin_api.route('/revert/finalized/grades/<int:latestBatchSemesterId>', methods=['PUT'])
@role_required('systemAdmin')
def updateFinalizedGrades(latestBatchSemesterId):
    print('latestBatchSemesterId: ', latestBatchSemesterId)
    university_admin = getCurrentUser()
    if university_admin:
        
        json_student_data_options = revertFinalizedGrades(latestBatchSemesterId)

        if json_student_data_options:
            return json_student_data_options
        else:
            return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404














@system_admin_api.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    # if user log status is not true (Auth server), then to log it in
    if not user:
        return redirect(url_for('home.home', next=request.url))
    if request.method == 'GET':
        try:
            grant = authorization.get_consent_grant(end_user=user)
        except OAuth2Error as error:
            return error.error
        return render_template('authorize.html', user=user, grant=grant)
    if not user and 'email' in request.form:
        email = request.form.get('email')
        user = SystemAdmin.query.filter_by(Email=email).first()
    if request.form['confirm']:
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]

