# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import UniversityAdmin

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required

# FUNCTIONS IMPORT
from .utils import getEnrollmentTrends, getCurrentGpaGiven, getOverallCoursePerformance, getAllClassData, getClassPerformance, getCurrentUser
import os

university_admin_api = Blueprint('university_admin_api', __name__)

@university_admin_api.route('/login', methods=['GET', 'POST'])
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
            return jsonify(message="No Performance data available")
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
