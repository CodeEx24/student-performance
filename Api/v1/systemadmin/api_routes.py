# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import SystemAdmin, OAuth2Client, db, Student, OAuth2Token
from authlib.oauth2 import OAuth2Error

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required
import time
from werkzeug.security import gen_salt
from oauth2 import authorization

from decorators.auth_decorators import preventAuthenticated, role_required

from .utils import getCurrentUser, getClientList, getClientsData, getAllClassData, getBatchSemester, getStudentData, getFacultyData, updateStudentData, getStudentAddOptions, revertFinalizedGrades, updateSystemAdminData, updatePassword, getStudentClassSubjectGrade, processGradeResubmission, updateGradesStudent, getStudentPerformance, processUpdatingStudents
from werkzeug.security import generate_password_hash

from flask_mail import Message
from mail import mail  # Import mail from the mail.py module
import secrets
from datetime import datetime, timedelta
import re
import os

system_admin_api_base_url = os.getenv("SYSTEM_ADMIN_API_BASE_URL")

system_admin_api = Blueprint('system_admin_api', __name__)


def current_user():
    if 'user_id' in session:
        uid = session['user_id']
        return SystemAdmin.query.get(uid)
    return None

# Login
@system_admin_api.route('/login', methods=['POST'])
# @login_decorator("Too many login attempts. Please try again later")
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
                return jsonify({'error': True, 'message': 'Invalid email format type'}), 401

            user = SystemAdmin.query.filter_by(Email=email).first()
                # Check for password
            if not user:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401
                
            if user and check_password_hash(user.Password, password):
                session['user_id'] = user.SysAdminId
                session['user_role'] = 'systemAdmin'
                user = current_user()
                return jsonify({"success": True, "message": "Login successful"}), 200
            else:
                # Return
                return jsonify({"error": True, "message": "Invalid email or password"}), 401
        except Exception as e:
            print('An exception occurred')
            return jsonify({"error": True, "message": "Invalid email or password"}), 401
    

@system_admin_api.route('/reset_password', methods=['POST'])
def forgotPassword():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': True, 'message': 'Please input an email'}), 401

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
        return jsonify({'error': True, 'message': 'Invalid email format type'}), 401
    
    # Check if email exists in the database
    systemAdmin = SystemAdmin.query.filter_by(Email=email).first()

    if not systemAdmin:
        # Intended so the intruder cannot be able to know whether email is registered or not
        return jsonify({'success': True, 'message': 'An email with instructions to reset your password has been sent to email.'}),200
        # return jsonify({'error': True, 'message': 'Email is invalid'}), 400

    if systemAdmin:
        # Generate a secure token
        token = secrets.token_hex(16)

        # Save the token and its expiration time in the database
        systemAdmin.Token = token
        systemAdmin.TokenExpiration = datetime.now() + timedelta(minutes=30)
        db.session.commit()

        # Send the reset email
        msg = Message('Password Reset Request', sender='your_email@example.com', recipients=[email])
        msg.body = f"Please click the following link to reset your password: {url_for('system_admin_api.resetPasswordConfirm', token=token, _external=True)}"
        mail.send(msg)
        flash('An email with instructions to reset your password has been sent.', 'info')
        return jsonify({'success': True, 'message': 'An email with instructions to reset your password has been sent to email.'}),200
    else:
        return jsonify({'error': True, 'message': 'Email is invalid'}), 400


# Step 6: Create a route to render the password reset confirmation form
@system_admin_api.route('/reset_password_confirm/<token>', methods=['GET'])
@preventAuthenticated
def resetPasswordConfirm(token):
    # Check if the token is valid and not expired
    systemAdmin = SystemAdmin.query.filter_by(Token=token).first()
    if systemAdmin and systemAdmin.TokenExpiration > datetime.now():
        return render_template('systemadmin/reset_password_confirm.html', token=token, system_admin_api_base_url=system_admin_api_base_url)
    else:
        flash('Invalid or expired token.', 'danger')
        return render_template('404.html')
# systemAdmin_api.py (continued)


# Step 8: Handle the form submission for resetting the password
@system_admin_api.route('/reset_password_confirm/<token>', methods=['POST'])
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
        systemAdmin = SystemAdmin.query.filter_by(Token=token).first()

        if systemAdmin and systemAdmin.TokenExpiration > datetime.now():
            # Update the password for the user in the database
            systemAdmin.Password = generate_password_hash(new_password)

            # Clear the token and expiration
            systemAdmin.Token = None
            systemAdmin.TokenExpiration = None

            db.session.commit()

            return jsonify({'message': 'Password reset successfully', 'status': 200})
        else:
            return jsonify({'message': 'Invalid or expired token', 'status': 400})



# Changing the password of the user
@system_admin_api.route('/change/password', methods=['POST'])
@role_required('systemAdmin')
def changePassword():
    print("ENTERING")
    
    system_admin = getCurrentUser()
    
    if system_admin:
        if request.method == 'POST':
            password = request.json.get('password')
            new_password = request.json.get('new_password')
            confirm_password = request.json.get('confirm_password')
            print("HGOUING")
            json_result = updatePassword(
                system_admin.SysAdminId, password, new_password, confirm_password)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404

# Make a client list route
@system_admin_api.route('/clients/', methods=['GET'])
@role_required('systemAdmin')
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
@role_required('systemAdmin')
def createClient():
    systemAdmin = current_user()
    print("CREATING CLIENT: ", systemAdmin)
    if request.method == "POST":
        try:
            print("SUPPOSED TO BE HERE2")
            if not systemAdmin:
                return redirect(url_for('systemAdminLogin'))
            print("SUPPOSED TO BE HERE1")
            client_id = gen_salt(24)
            client_id_issued_at = int(time.time())
            client = OAuth2Client(
                client_id=client_id,
                client_id_issued_at=client_id_issued_at,
                user_id=systemAdmin.SysAdminId,
            )
            print("SUPPOSED TO BE HERE")
            form = request.form
            print('form: ', form)
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
            return jsonify({'success': True, 'message': 'Adding client successfully'})
        except Exception as e:
            
          print('Error: ', e)
        
    
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
            return redirect(url_for('systemAdminClients'))
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
    systemAdmin = getCurrentUser()
    if systemAdmin:
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
    systemAdmin = getCurrentUser()
    if systemAdmin:
        
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
    systemAdmin = getCurrentUser()
    if systemAdmin:
        
        json_student_data_options = revertFinalizedGrades(latestBatchSemesterId)

        if json_student_data_options:
            return json_student_data_options
        else:
            return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


# Getting the student subject grade in a class
@system_admin_api.route('/class-subject-grade/', methods=['GET'])
@role_required('systemAdmin')
def studentClassSubjectGrade():
    systemAdmin = getCurrentUser()

    if systemAdmin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
      
        json_class_subject_grade = getStudentClassSubjectGrade(skip, top, order_by, filter)

        if json_class_subject_grade:
            return (json_class_subject_grade)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404

# Getting the student subject grade in a class
@system_admin_api.route('/class-subject-grade/$batch', methods=['POST'])
@role_required('systemAdmin')
def resubmitStudentClassSubjectGrade():
    print("HERE BATCG")
    systemAdmin = getCurrentUser()
    # Get all data in submission of frontend
    if systemAdmin:
        data = {'ClassSubjectId': 1343, 'LastName': 'Allena'}
        # Get tje data of POST request in syncfusion grid
        try:
            
            return jsonify({'sucess': True, 'result': data}), 200
        except Exception as e:
          print('An exception occurred: ', e)
          return jsonify({'sucess': True, 'result': data }), 200
    else:
        return render_template('404.html'), 404

# api_routes.py
@system_admin_api.route('/resubmit-grades', methods=['POST'])
@role_required('systemAdmin')
def submitGrades():
    systemAdmin = getCurrentUser()
    if systemAdmin:
        # Check if the request contains a file named 'excelFile'
        if 'excelFile' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['excelFile']

        # Call the utility function to process the file
        return processGradeResubmission(file)
    else:
        return render_template('404.html'), 404


# Getting the specific student performance
@system_admin_api.route('/student/performance/<string:id>', methods=['GET'])
@role_required('systemAdmin')
def studentPerformance(id):
    systemAdmin = getCurrentUser()
    if systemAdmin:
        json_student_performance = getStudentPerformance(id)

        if json_student_performance:
            return (json_student_performance)
        else:
            return jsonify({'error': True, 'message': "Something went wrong. Try to contact the admin to resolve the issue."})
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



# api_routes.py
@system_admin_api.route('/update-students', methods=['POST'])
@role_required('systemAdmin')
def updateStudents():
    systemAdmin = getCurrentUser()
    if systemAdmin:
            # Check if the request contains a file named 'excelFile'
        if 'excelFile' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['excelFile']

        # Call the utility function to process the file
        return processUpdatingStudents(file, excelType=True)
    else:
        return render_template('404.html'), 404
   