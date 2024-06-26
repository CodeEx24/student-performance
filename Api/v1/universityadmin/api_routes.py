# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import UniversityAdmin, db

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required

# FUNCTIONS IMPORT
from .utils import getEnrollmentTrends, getCurrentGpaGiven, getOverallCoursePerformance, getAllClassData, getClassPerformance, getCurrentUser, getUniversityAdminData, updateUniversityAdminData, updatePassword, processAddingStudents, getStudentData, processAddingClass, getAllClassSubjectData, getClassSubject, getClassDetails, getStudentClassSubjectData, getCurriculumData, getCurriculumSubject, processAddingCurriculumSubjects, getActiveTeacher, processUpdatingClassSubjectDetails, processAddingStudentInSubject, getMetadata, processClassStudents, deleteClassSubjectStudent, getCurriculumOptions, deleteCurriculumSubjectData, getStudentAddOptions, deleteStudentData, getClassListDropdown, getStudentClassSubjectGrade, getStudentPerformance, processGradeSubmission, getStatistics, getListersCount, deleteClassData, getBatchSemester, finalizedGradesBatchSemester, startEnrollmentProcess, getListerStudent, getListerTrends, getStudentList, createCriteria, getCriteriaList, getSpecificCriteriaData, getCriteriaOptions, getPassFailedAndDropout, getLatinHonorRates, getBatchLatest, getLatinHonors, getAllCourses

from datetime import datetime, timedelta
from decorators.auth_decorators import preventAuthenticated, role_required
from werkzeug.security import generate_password_hash
from flask_mail import Message
from mail import mail  # Import mail from the mail.py module

import os
import re
import secrets

university_admin_api_base_url = os.getenv("UNIVERSITY_ADMIN_API_BASE_URL")
university_admin_api = Blueprint('university_admin_api', __name__)

@university_admin_api.route('/login', methods=['POST'])
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
            
            admin = UniversityAdmin.query.filter_by(Email=email).first()
            if not admin:
                return jsonify({'error': True, 'message': 'Invalid email or password'}), 401
            
            if admin and check_password_hash(admin.Password, password):
                session['user_id'] = admin.UnivAdminId
                session['user_role'] = 'universityAdmin'
                return jsonify({"success": True, "message": "Login successful"}), 200
            else:
                # Return
                return jsonify({"error": True, "message": "Invalid email or password"}), 401
            # return redirect('/')
        except Exception as e:
            print('An exception occurred')
            return jsonify({"error": True, "message": "Invalid email or password"}), 401


@university_admin_api.route('/reset_password', methods=['POST'])
def forgotPassword():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': True, 'message': 'Please input an email'}), 401

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
        return jsonify({'error': True, 'message': 'Invalid email format type'}), 401
    
    # Check if email exists in the database
    universityAdmin = UniversityAdmin.query.filter_by(Email=email).first()

    if not universityAdmin:
        # Intended so the intruder cannot be able to know whether email is registered or not
        return jsonify({'success': True, 'message': 'An email with instructions to reset your password has been sent to email.'}),200
        # return jsonify({'error': True, 'message': 'Email is invalid'}), 400

    if universityAdmin:
        # Generate a secure token
        token = secrets.token_hex(16)

        # Save the token and its expiration time in the database
        universityAdmin.Token = token
        universityAdmin.TokenExpiration = datetime.now() + timedelta(minutes=30)
        db.session.commit()

        # Send the reset email
        msg = Message('Password Reset Request', sender='your_email@example.com', recipients=[email])
        msg.body = f"Please click the following link to reset your password: {url_for('university_admin_api.resetPasswordConfirm', token=token, _external=True)}"
        mail.send(msg)
        flash('An email with instructions to reset your password has been sent.', 'info')
        return jsonify({'success': True, 'message': 'An email with instructions to reset your password has been sent to email.'}),200
    else:
        return jsonify({'error': True, 'message': 'Email is invalid'}), 400


# Step 6: Create a route to render the password reset confirmation form
@university_admin_api.route('/reset_password_confirm/<token>', methods=['GET'])
@preventAuthenticated
def resetPasswordConfirm(token):
    # Check if the token is valid and not expired
    universityAdmin = UniversityAdmin.query.filter_by(Token=token).first()
    if universityAdmin and universityAdmin.TokenExpiration > datetime.now():
        return render_template('universityadmin/reset_password_confirm.html', token=token, university_admin_api_base_url=university_admin_api_base_url)
    else:
        flash('Invalid or expired token.', 'danger')
        return render_template('404.html')
# university_admin_api.py (continued)


# Step 8: Handle the form submission for resetting the password
@university_admin_api.route('/reset_password_confirm/<token>', methods=['POST'])
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
        universityAdmin = UniversityAdmin.query.filter_by(Token=token).first()

        if universityAdmin and universityAdmin.TokenExpiration > datetime.now():
            # Update the password for the user in the database
            universityAdmin.Password = generate_password_hash(new_password)

            # Clear the token and expiration
            universityAdmin.Token = None
            universityAdmin.TokenExpiration = None

            db.session.commit()

            return jsonify({'message': 'Password reset successfully', 'status': 200})
        else:
            return jsonify({'message': 'Invalid or expired token', 'status': 400})


# ===================================================
# TESTING AREA
@university_admin_api.route('/profile', methods=['GET'])
@role_required('universityAdmin')
def profile():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        return jsonify(universityAdmin.to_dict())
    else:
        flash('User not found', 'danger')
        return redirect(url_for('university_admin_api.login'))

# ===================================================

# Getting the user details
@university_admin_api.route('/', methods=['GET'])
@role_required('universityAdmin')
def universityAdminData():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_university_admin_data = getUniversityAdminData(universityAdmin.UnivAdminId)
        if json_university_admin_data:
            return (json_university_admin_data)
        else:
            return jsonify(message="No data available")
    else:
        return render_template('404.html'), 404

# Updating the user details
@university_admin_api.route('/details/update', methods=['POST'])
@role_required('universityAdmin')
def updateDetails():
    universityAdmin = getCurrentUser()
    print("ACCEPTED HERE")
    if universityAdmin:
        if request.method == 'POST':
            number = request.form.get('number')
            residential_address = request.form.get('residential-address')
          
            json_result = updateUniversityAdminData(universityAdmin.UnivAdminId, number, residential_address)
            return json_result
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))



# Changing the password of the user
@university_admin_api.route('/change/password', methods=['POST'])
@role_required('universityAdmin')
def changePassword():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        if request.method == 'POST':
            password = request.json.get('password')
            new_password = request.json.get('new_password')
            confirm_password = request.json.get('confirm_password')

            json_result = updatePassword(
                universityAdmin.UnivAdminId, password, new_password, confirm_password)

            return json_result

        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('studentLogin'))
    else:
        return render_template('404.html'), 404

# Getting the enrollment trends of different courses
@university_admin_api.route('/enrollment/trends', methods=['GET'])
@role_required('universityAdmin')
def enrollmentTrends():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_performance_data = getEnrollmentTrends()

        if json_performance_data:
            return (json_performance_data)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404
    
# Getting the enrollment trends of different courses
@university_admin_api.route('/lister/trends', methods=['GET'])
@role_required('universityAdmin')
def listerTrends():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_lister_data = getListerTrends()

        if json_lister_data:
            return (json_lister_data)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404


# Getting the Average GPA given
@university_admin_api.route('/current/gpa', methods=['GET'])
@role_required('universityAdmin')
def currentGpaGiven():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_current_gpa = getCurrentGpaGiven()

        if json_current_gpa:
            return (json_current_gpa)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404


# Getting the overall course performance
@university_admin_api.route('/overall/course/performance/<int:startYear>/<int:endYear>', methods=['GET'])
@role_required('universityAdmin')
def overallCoursePerformance(startYear, endYear):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_performance_data = getOverallCoursePerformance(startYear, endYear)

        if json_performance_data:
            return  json_performance_data
        else:
            return jsonify(error="No Performance data available")
    else:
        return render_template('404.html'), 404


@university_admin_api.route('/courses', methods=['GET'])
@role_required('universityAdmin')
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



# Getting all the class data in current year
@university_admin_api.route('/class/', methods=['GET'])
@role_required('universityAdmin')
def classData():
    universityAdmin = getCurrentUser()
    if universityAdmin:
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

@university_admin_api.route('/class/delete(<int:classId>)', methods=['DELETE'])
@role_required('universityAdmin')
def deleteClass(classId):
    university_admin = getCurrentUser()
    if university_admin:
        # result = classId
        result = deleteClassData(classId)
        return result
    else:
        return render_template('404.html'), 404


# Getting the specific class performance
@university_admin_api.route('/class/performance/<int:id>', methods=['GET', 'POST'])
@role_required('universityAdmin')
def classPerformance(id):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_class_performance = getClassPerformance(id)

        if json_class_performance:
            return (json_class_performance)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404



# api_routes.py
@university_admin_api.route('/submit-class', methods=['POST'])
@role_required('universityAdmin')
def submitClass():
    # Check if the request contains a file named 'excelFile'
    if 'excelFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['excelFile']

    # Call the utility function to process the file
    return processAddingClass(file)


# api_routes.py
@university_admin_api.route('/students/', methods=['GET'])
@role_required('universityAdmin')
def fetchStudents():
    university_admin = getCurrentUser()
    if university_admin:
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

# api_routes.py
@university_admin_api.route('/submit-students', methods=['POST'])
@role_required('universityAdmin')
def submitStudents():
    # Check if the request contains a file named 'excelFile'
    if 'excelFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['excelFile']

    # Call the utility function to process the file
    return processAddingStudents(file, excelType=True)

# api_routes.py
@university_admin_api.route('/student/options', methods=['GET'])
@role_required('universityAdmin')
def fetchStudentDataOptions():
    university_admin = getCurrentUser()
    if university_admin:
        
        json_student_data_options = getStudentAddOptions()

        if json_student_data_options:
            return (json_student_data_options)
        else:
            return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
    
    
@university_admin_api.route('/students/insert', methods=['POST'])
@role_required('universityAdmin')
def insertStudent():
    university_admin = getCurrentUser()
    if university_admin:
        data = request.json  # assuming the data is sent as JSON
        result = processAddingStudents(data)
        print('result: ', result)
        return result
    else:
        return render_template('404.html'), 404
    

@university_admin_api.route('/students/delete(<int:studentId>)', methods=['DELETE'])
@role_required('universityAdmin')
def deleteStudent(studentId):
    university_admin = getCurrentUser()
    if university_admin:
        result = deleteStudentData(studentId)
        print('result: ', result)
        return result
    else:
        return render_template('404.html'), 404

# Getting all the class data in current year
@university_admin_api.route('/class/subject', methods=['GET'])
@role_required('universityAdmin')
def classSubjectData():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_class_subject_data = getAllClassSubjectData()

        if json_class_subject_data:
            return (json_class_subject_data)
        else:
            return jsonify(message="No class subject data available")
    else:
        return render_template('404.html'), 404
    

# Getting all the class data in current year
@university_admin_api.route('/class/<int:class_id>', methods=['GET'])
@role_required('universityAdmin')
def fetchClassData(class_id):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_class_subject_data = getClassSubject(class_id)

        if json_class_subject_data:
            return (json_class_subject_data)
        else:
            return jsonify(message="No class subject data available")
    else:
        return render_template('404.html'), 404
    
    
@university_admin_api.route('/class/details/<int:class_id>', methods=['GET'])
@role_required('universityAdmin')
def fetchClassDetails(class_id):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_class_details = getClassDetails(class_id)

        if json_class_details:
            return (json_class_details)
        else:
            return jsonify(message="No class subject data available")
    else:
        return render_template('404.html'), 404
    
@university_admin_api.route('/class/subject/<int:class_subject_id>/', methods=['GET'])
@role_required('universityAdmin')
def fetchStudentClassSubjectData(class_subject_id):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_class_subject_data = getStudentClassSubjectData(class_subject_id, skip, top, order_by, filter)
        print('json_class_subject_data: ', json_class_subject_data)
        if json_class_subject_data:
            return (json_class_subject_data)
        else:
            return jsonify(message="No class subject data available"), 400
    else:
        return render_template('404.html'), 404


# Getting the student subject grade in a class
@university_admin_api.route('/class-subject-grade/', methods=['GET'])
@role_required('universityAdmin')
def studentClassSubjectGrade():
    universityAdmin = getCurrentUser()

    if universityAdmin:
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

# Getting the specific student performance
@university_admin_api.route('/student/performance/<string:id>', methods=['GET', 'POST'])
@role_required('universityAdmin')
def studentPerformance(id):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_student_performance = getStudentPerformance(id)

        if json_student_performance:
            return (json_student_performance)
        else:
            return jsonify({'error': True, 'message': "Something went wrong. Try to contact the admin to resolve the issue."})
    else:
        return render_template('404.html'), 404

# api_routes.py
@university_admin_api.route('/submit-grades', methods=['POST'])
@role_required('universityAdmin')
def submitGrades():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        # Check if the request contains a file named 'excelFile'
        if 'excelFile' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['excelFile']

        # Call the utility function to process the file
        return processGradeSubmission(file)
    else:
        return render_template('404.html'), 404

# DOING HERE
@university_admin_api.route('/class/subject/<int:class_subject_id>/insert', methods=['POST'])
@role_required('universityAdmin')
def studentClassSubjectInsert(class_subject_id):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        data = request.json  # assuming the data is sent as JSON
        result = processAddingStudentInSubject(data, class_subject_id)
        return result
    else:
        return render_template('404.html'), 404
    
# DOING HERE
@university_admin_api.route('/class/subject/<int:class_subject_id>/delete(<int:student_id>)', methods=['DELETE'])
@role_required('universityAdmin')
def studentClassSubjectDelete(class_subject_id, student_id):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        result = deleteClassSubjectStudent(class_subject_id, student_id)
        return result
    else:
        return render_template('404.html'), 404


    
    
@university_admin_api.route('/curriculum/', methods=['GET'])
@role_required('universityAdmin')
def fetchCurriculum():
    universityAdmin = getCurrentUser()
    
    if universityAdmin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_curriculum_data = getCurriculumData(skip, top, order_by, filter)
        print('json_curriculum_data: ', json_curriculum_data)
        if json_curriculum_data:
            print('json_curriculum_data: ', json_curriculum_data)
            return (json_curriculum_data)
        else:
            return jsonify(message="No curriculum data available"), 400
    else:
        return render_template('404.html'), 404
    
@university_admin_api.route('/curriculum/options', methods=['GET'])
@role_required('universityAdmin')
def fetchCurriculumOptions():
    universityAdmin = getCurrentUser()
    if universityAdmin:

        json_curriculum_options = getCurriculumOptions()
        if json_curriculum_options:
            return (json_curriculum_options)
        else:
            return jsonify(message="No curriculum data available"), 400
    else:
        return render_template('404.html'), 404
    
    
@university_admin_api.route('/curriculum/insert', methods=['POST'])
@role_required('universityAdmin')
def insertCurriculumSubject():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        data = request.json  # assuming the data is sent as JSON
        result = processAddingCurriculumSubjects(data)
        return result
    else:
        return render_template('404.html'), 404        
    
    
@university_admin_api.route('/curriculum/delete(<int:curriculumId>)', methods=['DELETE'])
@role_required('universityAdmin')
def deleteCurriculumSubject(curriculumId):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        print('curriculumId: ', curriculumId)
        # data = request.json  # assuming the data is sent as JSON
        result = deleteCurriculumSubjectData(curriculumId)
        return result
    else:
        return render_template('404.html'), 404        
    
@university_admin_api.route('/active/teacher', methods=['GET'])
@role_required('universityAdmin')
def fetchActiveTeacher():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_active_teacher_data = getActiveTeacher()

        if json_active_teacher_data:
            return (json_active_teacher_data)
        else:
            return jsonify(message="No active teacher data available"), 400
    else:
        return render_template('404.html'), 404
        


@university_admin_api.route('/curriculum/subjects/<int:metadata_id>', methods=['GET'])
@role_required('universityAdmin')
def fetchCurriculumSubjects(metadata_id):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_class_subject_data = getCurriculumSubject(metadata_id)

        if json_class_subject_data:
            return (json_class_subject_data)
        else:
            return jsonify(message="No class subject data available"), 400
    else:
        return render_template('404.html'), 404    
    

@university_admin_api.route('/submit-curriculum-subjects', methods=['POST'])
@role_required('universityAdmin')
def submitCurriculumSubjects():
    # Check if method is post
    if request.method == 'POST':
        universityAdmin = getCurrentUser()
        if universityAdmin:
            if 'excelFile' in request.files:
                file = request.files['excelFile']
                result = processAddingCurriculumSubjects(file, True)
                # Call the utility function to process the file
                return result
            # else if request.get_json() has a data
            elif request.get_json():
                data = request.get_json()
                print('data: ', data)
                result = processAddingCurriculumSubjects(data)
                # Call the utility function to process the file
                return result
            else:
                if 'excelFile' not in request.files:
                    return jsonify({'error': 'No file part'}), 400
                else:
                    return jsonify({'error': 'Something went wrong'}), 400
        else:
            return render_template('404.html'), 404
    


    
    
@university_admin_api.route('/update/class-subject', methods=['POST'])
@role_required('universityAdmin')
def updateClassSubject():
    universityAdmin = getCurrentUser()
    data = request.json  # assuming the data is sent as JSON

    if universityAdmin:
        return processUpdatingClassSubjectDetails(data)
    else:
        return render_template('404.html'), 404    



# api_routes.py
@university_admin_api.route('/submit/students-subject/<int:class_subject_id>', methods=['POST'])
@role_required('universityAdmin')
def submitStudentsClassSubject(class_subject_id):

    universityAdmin = getCurrentUser()
    if universityAdmin:
        if 'studentSubjectExcel' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['studentSubjectExcel']
        # Call the utility function to process the file
    
        return processAddingStudentInSubject(file, class_subject_id, excelType=True)
    else:
        return render_template('404.html'), 404    
    
    
@university_admin_api.route('/passing-drop-withdrawn-and-failed/<int:programId>/<int:startingYear>/<int:endingYear>', methods=['GET'])
@role_required('universityAdmin')
def fetchPassFailedAndDropout(programId, startingYear, endingYear):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        return getPassFailedAndDropout(programId, startingYear, endingYear)
    else:
        return render_template('404.html'), 404    
    
@university_admin_api.route('/batch/latest', methods=['GET'])
@role_required('universityAdmin')
def fetchBatchLatest():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        return getBatchLatest()
    else:
        return render_template('404.html'), 404   
    

@university_admin_api.route('/latin-honors/rates/<int:year>', methods=['GET'])
@role_required('universityAdmin')
def latinHonorRates(year):
    universityAdmin = getCurrentUser()
    if universityAdmin:
        return getLatinHonorRates(year)
    else:
        return render_template('404.html'), 404    
    

# api_routes.py
@university_admin_api.route('/metadata/', methods=['GET'])
@role_required('universityAdmin')
def fetchMetadata():
    university_admin = getCurrentUser()
    if university_admin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_student_data = getMetadata(skip, top, order_by, filter)

        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
    

# api_routes.py
@university_admin_api.route('/latin/honors/', methods=['GET'])
@role_required('universityAdmin')
def fetchLatinHonors():
    university_admin = getCurrentUser()
    if university_admin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = (request.args.get('$orderby'))
        filter = (request.args.get('$filter'))
        
        json_latin_honors_data = getLatinHonors(skip, top, order_by, filter)

        if json_latin_honors_data:
            return (json_latin_honors_data)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
    

# api_routes.py
@university_admin_api.route('/finalized/batch/', methods=['GET'])
@role_required('universityAdmin')
def fetchBatchSemester():
    university_admin = getCurrentUser()
    if university_admin:
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
@university_admin_api.route('/add/class-student/<int:class_id>', methods=['POST'])
@role_required('universityAdmin')
def submitClassStudents(class_id):
    university_admin = getCurrentUser()
    if university_admin:
        if 'classStudentsExcel' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['classStudentsExcel']
        
        json_student_data = processClassStudents(file, class_id)

        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404


@university_admin_api.route('/finalized/grades/batch', methods=['POST'])
@role_required('universityAdmin')
def finalizedGradesBatch():
    # Check if method is post
    if request.method == 'POST':
        universityAdmin = getCurrentUser()
        if universityAdmin:
            batch_semester_id = request.form['batchSemester']
            honors_criteria_id = request.form['criteriaOption']
            json_student_data = finalizedGradesBatchSemester(batch_semester_id, honors_criteria_id)
            if json_student_data:
                return (json_student_data)
            else:
                return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
        else:
            return render_template('404.html'), 404
    
    
@university_admin_api.route('/start/enrollment/<int:batch_semester_id>', methods=['PUT'])
@role_required('universityAdmin')
def startEnrollment(batch_semester_id):
    university_admin = getCurrentUser()
    if university_admin:
        json_student_data = startEnrollmentProcess(batch_semester_id)

        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
    
    
# api_routes.py
# ?batch=value
@university_admin_api.route('/class/dropdown', methods=['GET'])
def fetchClassDropdown():
    # Check if batch already have value
    batch = request.args.get('batch')
    if batch:
        class_list = getClassListDropdown(True)
    else:
        class_list = getClassListDropdown()

    if class_list:
        return (class_list)
    else:
        return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")


@university_admin_api.route('/statistics', methods=['GET'])
@role_required('universityAdmin')
def fetchStatistics():
    university_admin = getCurrentUser()
    print("CURRENT USER: ", university_admin)
    if university_admin:
        class_list = getStatistics()
        # return class list
        if class_list:
            return (class_list)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    

@university_admin_api.route('/listers/count', methods=['GET'])
@role_required('universityAdmin')
def fetchListers():
    university_admin = getCurrentUser()
    if university_admin:
        listers_data = getListersCount()
        # return class list
        if listers_data:
            return (listers_data)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")


    
@university_admin_api.route('/student/listers/', methods=['GET'])
def fetchListersStudents():
    university_admin = getCurrentUser()
    if university_admin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = request.args.get('$orderby')
        filter = request.args.get('$filter')
        print("HERE IN BACKEND")
        student_achievement_list = getListerStudent(skip, top, order_by, filter)
        if student_achievement_list:
            return student_achievement_list
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    
    
@university_admin_api.route('/submit/criteria', methods=['POST'])
def submitCriteria():
     if request.method == 'POST':
        university_admin = getCurrentUser()
        if university_admin:
            try:
                return createCriteria(request.form)
            except Exception as e:
                print('An exception occurred')
                return jsonify({"error": True, "message": "Invalid email or password"}), 401
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")

      
@university_admin_api.route('/criteria/', methods=['GET'])
def getCriteria():
    university_admin = getCurrentUser()
    if university_admin:
        skip = int(request.args.get('$skip', 0))
        top = int(request.args.get('$top', 10))
        order_by = request.args.get('$orderby')
        filter = request.args.get('$filter')
        
        student_achievement_list = getCriteriaList(skip, top, order_by, filter)
        if student_achievement_list:
            return student_achievement_list
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    
@university_admin_api.route('/criteria/<int:criteriaId>', methods=['GET'])
def getSpecificCriteria(criteriaId):
    university_admin = getCurrentUser()
    if university_admin:
        print("criteriaId: ", criteriaId)
        
        criteria_data = getSpecificCriteriaData(criteriaId)
        if criteria_data:
            return criteria_data
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")

@university_admin_api.route('/criteria-option/<int:semester>', methods=['GET'])
def getSemesterOptionCriteria(semester):
    university_admin = getCurrentUser()
    if university_admin:
        print("criteriaId: ", semester)
        
        criteria_options_data = getCriteriaOptions(semester)
        if criteria_options_data:
            return criteria_options_data
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")


   

# Get enc STATIC_TOKEN
STATIC_TOKEN = "1b20e3f9-8d44-45b7-96da-02e8001d73e8"

@university_admin_api.route('/student/achievement/', methods=['GET'])
def studentAchievement():
    # Check if the 'Authorization' header is present
    if 'X-API-Key' not in request.headers:
        return "API key is missing", 401
    # Get the token from the 'Authorization' header
    token = request.headers['X-API-Key']
    
    if token != STATIC_TOKEN:
        return "Invalid token", 403
    
    skip = int(request.args.get('$skip', 0))
    top = int(request.args.get('$top', 10))
    order_by = request.args.get('$orderby')
    filter = request.args.get('$filter')
    
    student_achievement_list = getListerStudent(skip, top, order_by, filter)
    
    return (student_achievement_list)


# api_routes.py
@university_admin_api.route('/student/', methods=['GET'])
def fetchPublicStudents():
    # Check if the 'Authorization' header is present
    if 'X-API-Key' not in request.headers:
        return "API key is missing", 401
    # Get the token from the 'Authorization' header
    token = request.headers['X-API-Key']
    
    if token != STATIC_TOKEN:
        return "Invalid token", 403
    
    skip = int(request.args.get('$skip', 0))
    top = int(request.args.get('$top', 10))
    order_by = request.args.get('$orderby')
    filter = request.args.get('$filter')
        
    json_student_data = getStudentList(skip, top, order_by, filter)

    if json_student_data:
        return (json_student_data)
    else:
        return jsonify(error="Something went wrong. Try to contact the admin to resolve the issue.")
    
