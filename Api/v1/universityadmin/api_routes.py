# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import UniversityAdmin

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required

# FUNCTIONS IMPORT
from .utils import getEnrollmentTrends, getCurrentGpaGiven, getOverallCoursePerformance, getAllClassData, getClassPerformance, getCurrentUser, getUniversityAdminData, updateUniversityAdminData, updatePassword, processAddingStudents, getStudentData, processAddingClass, getAllClassSubjectData, getClassSubject, getClassDetails, getStudentClassSubjectData, getCurriculumData, getCurriculumSubject, processAddingCurriculumSubjects, getActiveTeacher, processUpdatingClassSubjectDetails, processAddingStudentInSubject, getMetadata, finalizedGradesReport, processClassStudents, deleteClassSubjectStudent, getCurriculumOptions, deleteCurriculumSubjectData, getStudentAddOptions, deleteStudentData, getClassListDropdown, getStudentClassSubjectGrade, getStudentPerformance, processGradeSubmission, getStatistics, getListersCount
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
            return  json_performance_data
        else:
            return jsonify(error="No Performance data available")
    else:
        return render_template('404.html'), 404


# Getting all the class data in current year
@university_admin_api.route('/class/data/', methods=['GET'])
@role_required('universityAdmin')
def classData():
    universityAdmin = getCurrentUser()
    if universityAdmin:
        skip = int(request.args.get('$skip', 1))
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
        skip = int(request.args.get('$skip', 1))
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
        skip = int(request.args.get('$skip', 1))
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
        skip = int(request.args.get('$skip', 1))
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
    

# api_routes.py
@university_admin_api.route('/metadata/', methods=['GET'])
@role_required('universityAdmin')
def fetchMetadata():
    university_admin = getCurrentUser()
    if university_admin:
        skip = int(request.args.get('$skip', 1))
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
