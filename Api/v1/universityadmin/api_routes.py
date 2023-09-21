# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import UniversityAdmin

from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from decorators.auth_decorators import universityAdminRequired

# FUNCTIONS IMPORT
from .utils import getEnrollmentTrends, getCurrentGpaGiven, getOverallCoursePerformance, getAllClassData, getClassPerformance
import os

university_admin_api = Blueprint('university_admin_api', __name__)

# Api/v1/admin/api_routes.py
# Access API keys from environment variables
WEBSITE1_API_KEY = os.getenv('WEBSITE1_API_KEY')
WEBSITE2_API_KEY = os.getenv('WEBSITE2_API_KEY')
WEBSITE3_API_KEY = os.getenv('WEBSITE3_API_KEY')
WEBSITE4_API_KEY = os.getenv('WEBSITE4_API_KEY')
WEBSITE5_API_KEY = os.getenv('WEBSITE5_API_KEY')
university_admin_api_key = os.getenv('UNIVERSITY_ADMIN_API_KEY')


API_KEYS = {
    'website1': WEBSITE1_API_KEY,
    'website2': WEBSITE2_API_KEY,
    'website3': WEBSITE3_API_KEY,
    'website4': WEBSITE4_API_KEY,
    'website5': WEBSITE5_API_KEY,
    'university_admin_key': university_admin_api_key
}


@university_admin_api.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        admin = UniversityAdmin.query.filter_by(Email=email).first()
        if admin and check_password_hash(admin.Password, password):
            # Successfully authenticated
            access_token = create_access_token(identity=admin.UnivAdminId)
            session['access_token'] = access_token
            session['user_role'] = 'universityAdmin'
            session['admin_number'] = admin.UnivAdminNumber
            return redirect(url_for('universityAdminHome'))
        else:
            flash('Invalid email or password', 'danger')
    return redirect(url_for('universityAdminLogin'))


# ===================================================
# TESTING AREA
@university_admin_api.route('/profile', methods=['GET'])
@universityAdminRequired
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    admin = UniversityAdmin.query.get(current_user_id)
    if admin:
        return jsonify(admin.to_dict())
    else:
        flash('User not found', 'danger')
        return redirect(url_for('university_admin_api.login'))

# ===================================================


# Getting the enrollment trends of different courses
@university_admin_api.route('/enrollment/trends', methods=['GET'])
def enrollmentTrends():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():

        json_performance_data = getEnrollmentTrends()

        if json_performance_data:
            return (json_performance_data)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404


# Getting the Average GPA given
@university_admin_api.route('/current/gpa', methods=['GET'])
def currentGpaGiven():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        json_current_gpa = getCurrentGpaGiven()

        if json_current_gpa:
            return (json_current_gpa)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404


# Getting the overall course performance
@university_admin_api.route('/overall/course/performance', methods=['GET'])
def overallCoursePerformance():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        json_performance_data = getOverallCoursePerformance()

        if json_performance_data:
            return (json_performance_data)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404


# Getting all the class data in current year
@university_admin_api.route('/class/data', methods=['GET'])
def classData():
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        json_class_data = getAllClassData()

        if json_class_data:
            return (json_class_data)
        else:
            return jsonify(message="No Performance data available")
    else:
        return render_template('404.html'), 404


# Getting the specific class performance
@university_admin_api.route('/class/performance/<int:id>', methods=['GET', 'POST'])
def classPerformance(id):
    api_key = request.headers.get('X-Api-Key')
    if api_key in API_KEYS.values():
        json_class_performance = getClassPerformance(id)

        if json_class_performance:
            return (json_class_performance)
        else:
            return jsonify(message="Something went wrong. Try to contact the admin to resolve the issue.")
    else:
        return render_template('404.html'), 404
