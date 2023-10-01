
from flask import Flask, render_template, redirect, url_for, session
from flask_caching import Cache
from flask_cors import CORS

from Api.v1.student.api_routes import student_api
from Api.v1.faculty.api_routes import faculty_api
from Api.v1.universityadmin.api_routes import university_admin_api

import os
from dotenv import load_dotenv

from models import init_db, Student, Faculty, UniversityAdmin
from flask_jwt_extended import JWTManager
from decorators.auth_decorators import studentRequired, facultyRequired, preventAuthenticated, universityAdminRequired
from datetime import datetime, timedelta

def create_app():
    load_dotenv()  # Load environment variables from .env file
    app = Flask(__name__)

    # SETUP YOUR POSTGRE DATABASE HERE
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    # Replace 'your-secret-key' with an actual secret key
    app.secret_key = os.getenv('SECRET_KEY')
    Cache(app, config={'CACHE_TYPE': 'simple'})
    # cache.init_app(app)

    CORS(app)
    jwt = JWTManager(app)
    init_db(app)

    # The Api Key is static for development mode. The Api key in future must refresh in order to secure the api endpoint of the application
    # student_api_key = os.getenv('STUDENT_API_KEY')
    # faculty_api_key = os.getenv('FACULTY_API_KEY')
    university_admin_api_key = os.getenv('UNIVERSITY_ADMIN_API_KEY')
    # system_admin_api_key = os.getenv('SYSTEM_ADMIN_API_KEY')

    # The api base url for api endpoints
    student_api_base_url = os.getenv("STUDENT_API_BASE_URL")
    faculty_api_base_url = os.getenv("FACULTY_API_BASE_URL")
    university_admin_api_base_url = os.getenv("UNIVERSITY_ADMIN_API_BASE_URL")


    @app.context_processor
    def custom_context_processor():
        authenticated = False
        if 'user_role' in session:
            authenticated = True
        return {'authenticated': authenticated}

    # @app.after_request
    # def remove_headers(response):
    #     for key in response.headers:
    #         response.headers[key] = None

    #     return response

    # ===========================================================================
    # ROUTING FOR THE APPLICATION (http:localhost:3000)


    @app.route('/')
    @preventAuthenticated
    def home():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('main/index.html')


    @app.route('/logout')
    def logout():
        # Clear session data including JWT token and user role
        session.clear()
        return redirect(url_for('home'))  # Redirect to home or appropriate route

    # ========================================================================


    # ALL STUDENT ROUTES HERE
    @app.route('/student')
    @preventAuthenticated
    def studentLogin():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('student/login.html')


    @app.route('/student/home')
    @studentRequired
    def studentHome():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('student/home.html', student_api_base_url=student_api_base_url, current_page="home", access_token=session['access_token'])


    @app.route('/student/grade')
    @studentRequired
    def studentGrade():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('student/grades.html', student_api_base_url=student_api_base_url, current_page="grades")


    @app.route('/student/profile')
    @studentRequired
    def studentProfile():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('student/profile.html', student_api_base_url=student_api_base_url, current_page="profile")


    @app.route('/student/change-password')
    @studentRequired
    def changePassword():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('student/change_password.html', student_api_base_url=student_api_base_url,  current_page="change-password")


    # ========================================================================


    # ALL FACULTY ROUTES HERE
    @app.route('/faculty')
    @preventAuthenticated
    def facultyLogin():
        return render_template('faculty/login.html')


    @app.route('/faculty/dashboard')
    @facultyRequired
    def facultyHome():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('faculty/dashboard.html', faculty_api_base_url=faculty_api_base_url, current_page="dashboard", access_token=session['access_token'])


    @app.route('/faculty/grades')
    @facultyRequired
    def facultyGrades():
        session['last_interaction_time'] = datetime.utcnow()
        print(session['access_token'])
        return render_template('faculty/grades.html', faculty_api_base_url=faculty_api_base_url, current_page="grades")


    @app.route('/faculty/class-comparison')
    @facultyRequired
    def facultyClassComparison():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('faculty/class-comparison.html', faculty_api_base_url=faculty_api_base_url, current_page="class-comparison")


    @app.route('/faculty/profile')
    @facultyRequired
    def facultyProfile():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('faculty/profile.html', faculty_api_base_url=faculty_api_base_url, current_page="profile")


    @app.route('/faculty/change-password')
    @facultyRequired
    def facultyChangePassword():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('faculty/change_password.html', faculty_api_base_url=faculty_api_base_url, current_page="change-password")


    # ========================================================================


    # ALL UNIVERSITY ADMIN ROUTES HERE
    @app.route('/university-admin')
    @preventAuthenticated
    def universityAdminLogin():
        return render_template('universityadmin/login.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url)


    @app.route('/university-admin/home')
    @universityAdminRequired
    def universityAdminHome():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('universityadmin/home.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url, current_page="home")


    @app.route('/university-admin/class-performance')
    @universityAdminRequired
    def universityClassPerformance():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('universityadmin/class-performance.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url, current_page="class-performance")


    @app.route('/university-admin/profile')
    @universityAdminRequired
    def universityProfile():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('universityadmin/profile.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url, current_page="profile")


    @app.route('/university-admin/change-password')
    @universityAdminRequired
    def universityChangePassword():
        session['last_interaction_time'] = datetime.utcnow()
        return render_template('universityadmin/change-password.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url, current_page="change-password")


    # ========================================================================
    # Register the API blueprint
    app.register_blueprint(university_admin_api, url_prefix='/api/v1/university-admin')
    app.register_blueprint(faculty_api, url_prefix='/api/v1/faculty')
    app.register_blueprint(student_api, url_prefix='/api/v1/student')
    


    @app.route('/page_not_found')  # Define an actual route
    def page_not_found():
        return handle_404_error(None)


    @app.errorhandler(404)
    def handle_404_error(e):
        return render_template('404.html'), 404

    return app


    