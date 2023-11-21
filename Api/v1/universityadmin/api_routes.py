# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import UniversityAdmin

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required

# FUNCTIONS IMPORT
from .utils import getEnrollmentTrends, getCurrentGpaGiven, getOverallCoursePerformance, getAllClassData, getClassPerformance, getCurrentUser, getUniversityAdminData, updateUniversityAdminData, updatePassword, processAddingStudents, getStudentData, processAddingClass, getAllClassSubjectData, getClassSubject, getClassDetails, getStudentClassSubjectData, getCurriculumData, getCurriculumSubject, processAddingCurriculumSubjects, getActiveTeacher, processUpdatingClassSubjectDetails, processAddingStudentInSubject, getMetadata, finalizedGradesReport, processClassStudents, deleteStudent
import os


university_admin_api = Blueprint('university_admin_api', __name__)

@university_admin_api.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin = UniversityAdmin.query.filter_by(Email=email).first()
        if admin and check_password_hash(admin.Password, password):
            session['user_id'] = admin.UnivAdminId
            session['user_role'] = 'universityAdmin'
            return redirect(url_for('universityAdminHome'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('universityAdminLogin'))
    return redirect(url_for('universityAdminLogin'))

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
    if universityAdmin:
        if request.method == 'POST':
            print("HERE POSTING")
            email = request.json.get('email')
            number = request.json.get('number')
            residentialAddress = request.json.get('residentialAddress')

            json_result = updateUniversityAdminData(
                universityAdmin.UnivAdminId, email, number, residentialAddress)

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
@university_admin_api.route('/overall/course/performance', methods=['GET'])
@role_required('universityAdmin')
def overallCoursePerformance():
    universityAdmin = getCurrentUser()
    
    if universityAdmin:
        json_performance_data = getOverallCoursePerformance()

        if json_performance_data:
            return (json_performance_data)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404


# Getting all the class data in current year
@university_admin_api.route('/class/data', methods=['GET'])
@role_required('universityAdmin')
def classData():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_class_data = getAllClassData()

        if json_class_data:
            return (json_class_data)
        else:
            return jsonify(message="No Class data available")
    else:
        return render_template('404.html'), 404


# Getting the specific class performance
@university_admin_api.route('/class/performance/<int:id>', methods=['GET', 'POST'])
@role_required('universityAdmin')
def classPerformance(id):
    print("THE ID: ", id)
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_class_performance = getClassPerformance(id)
        print("json_class_performance: ", json_class_performance)

        if json_class_performance:
            return (json_class_performance)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404

# api_routes.py
@university_admin_api.route('/submit-students', methods=['POST'])
@role_required('universityAdmin')
def submitStudents():
    # print("IN UNIVERSITY ADMIN STUDENTS SERVER")
    # print("REQUEST FILES: ", request.files)
    # Check if the request contains a file named 'excelFile'
    if 'excelFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['excelFile']

    # Call the utility function to process the file
    return processAddingStudents(file)

# api_routes.py
@university_admin_api.route('/submit-class', methods=['POST'])
@role_required('universityAdmin')
def submitClass():
    print("IN UNIVERSITY ADMIN STUDENTS SERVER")
    print("REQUEST FILES: ", request.files)
    # Check if the request contains a file named 'excelFile'
    if 'excelFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['excelFile']

    # Call the utility function to process the file
    return processAddingClass(file)


# api_routes.py
@university_admin_api.route('/students', methods=['GET'])
@role_required('universityAdmin')
def fetchStudents():
    university_admin = getCurrentUser()
    if university_admin:
        json_student_data = getStudentData()

        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
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
    print("GETTING THE CLASS SUBJECT")
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
    

@university_admin_api.route('/class/subject/<int:class_subject_id>', methods=['GET'])
@role_required('universityAdmin')
def fetchStudentClassSubjectData(class_subject_id):
    print("HERE IN CLASS SUBJECT")
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_class_subject_data = getStudentClassSubjectData(class_subject_id)
        print('json_class_subject_data: ', json_class_subject_data)
        if json_class_subject_data:
            return (json_class_subject_data)
        else:
            return jsonify(message="No class subject data available"), 400
    else:
        return render_template('404.html'), 404

@university_admin_api.route('/delete/class-subject/<int:class_subject_id>/student/<int:student_id>', methods=['POST'])
@role_required('universityAdmin')
def deleteClassSubjectStudents(class_subject_id, student_id):
    print("HERE IN CLASS SUBJECT")
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_class_subject_data = deleteStudent(class_subject_id, student_id)
        print('json_class_subject_data: ', json_class_subject_data)
        if json_class_subject_data:
            return (json_class_subject_data)
        else:
            return jsonify(message="No class subject data available"), 400
    else:
        return render_template('404.html'), 404
    
    
@university_admin_api.route('/curriculum', methods=['GET'])
@role_required('universityAdmin')
def fetchCurriculum():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        json_curriculum_data = getCurriculumData()

        if json_curriculum_data:
            return (json_curriculum_data)
        else:
            return jsonify(message="No class subject data available"), 400
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
    print("HERE IN CURRICULUM SUBJECTS")
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
    print("HERE IN CURRICULUM SUBJECTS")
    universityAdmin = getCurrentUser()
    if universityAdmin:
        if 'excelFile' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['excelFile']
        # print(processAddingCurriculumSubjects(file))
        # Call the utility function to process the file
        return processAddingCurriculumSubjects(file)
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
    print("class_subject_id: ", class_subject_id)
    print("REQUEST FILES: ", request.files)
    universityAdmin = getCurrentUser()
    if universityAdmin:
        if 'studentSubjectExcel' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['studentSubjectExcel']
        # print(processAddingCurriculumSubjects(file))
        # Call the utility function to process the file
    
        # print('=================================================')
        # print('data, status_code: ', data)
        return processAddingStudentInSubject(file, class_subject_id)
    else:
        return render_template('404.html'), 404    
    

# api_routes.py
@university_admin_api.route('/metadata', methods=['GET'])
@role_required('universityAdmin')
def fetchMetadata():
    university_admin = getCurrentUser()
    if university_admin:
        json_student_data = getMetadata()

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

# Finalized grades routes
@university_admin_api.route('/finalized/grades/<int:metadata_id>', methods=['GET'])
@role_required('universityAdmin')
def finalizedGrades(metadata_id):
    university_admin = getCurrentUser()
    if university_admin:
        json_student_data = finalizedGradesReport(metadata_id)

        if json_student_data:
            return (json_student_data)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404