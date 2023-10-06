
from flask import Flask, render_template, redirect, url_for, session
from flask_caching import Cache
from flask_cors import CORS

from Api.v1.student.api_routes import student_api
from Api.v1.faculty.api_routes import faculty_api
from Api.v1.universityadmin.api_routes import university_admin_api


import os
from dotenv import load_dotenv

from models import init_db
from flask_jwt_extended import JWTManager

from decorators.auth_decorators import preventAuthenticated, role_required
from datetime import  timedelta

def create_app():
    load_dotenv()  # Load environment variables from .env file
    app = Flask(__name__)

    # SETUP YOUR POSTGRE DATABASE HERE
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Replace 'your-secret-key' with an actual secret key
    app.secret_key = os.getenv('SECRET_KEY')
    Cache(app, config={'CACHE_TYPE': 'simple'})
    # cache.init_app(app)

    # Allowed third party apps
    allowed_origins = ["https://example1.com", "https://example2.com"]
    CORS(app, origins=allowed_origins, allow_headers=["Authorization", "X-API-Key"])

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
    
    @app.before_request
    def before_request():
        session.permanent=True
        pass
    
    # ===========================================================================
    # ROUTING FOR THE APPLICATION (http:localhost:3000)


    @app.route('/')
    @preventAuthenticated
    def home():
        return render_template('main/index.html')


    @app.route('/logout')
    def logout():
        # session.removeItem('access_token')
        
        session.clear()
        return redirect(url_for('home'))  # Redirect to home or appropriate route

    # ========================================================================


    # ALL STUDENT ROUTES HERE
    @app.route('/student')
    @preventAuthenticated
    def studentLogin():
        return render_template('student/login.html')


    @app.route('/student/home')
    @role_required('student')
    def studentHome():
        return render_template('student/home.html', student_api_base_url=student_api_base_url, current_page="home")


    @app.route('/student/grade')
    @role_required('student')
    def studentGrade():
        return render_template('student/grades.html', student_api_base_url=student_api_base_url, current_page="grades")


    @app.route('/student/profile')
    @role_required('student')
    def studentProfile():
        return render_template('student/profile.html', student_api_base_url=student_api_base_url, current_page="profile")


    @app.route('/student/change-password')
    @role_required('student')
    def changePassword():
        return render_template('student/change_password.html', student_api_base_url=student_api_base_url,  current_page="change-password")


    # ========================================================================


    # ALL FACULTY ROUTES HERE
    @app.route('/faculty')
    @preventAuthenticated
    def facultyLogin():
        return render_template('faculty/login.html')


    @app.route('/faculty/dashboard')
    @role_required('faculty')
    def facultyHome():
        return render_template('faculty/dashboard.html', faculty_api_base_url=faculty_api_base_url, current_page="dashboard")


    @app.route('/faculty/grades')
    @role_required('faculty')
    def facultyGrades():
        return render_template('faculty/grades.html', faculty_api_base_url=faculty_api_base_url, current_page="grades")


    @app.route('/faculty/class-comparison')
    @role_required('faculty')
    def facultyClassComparison():
        return render_template('faculty/class-comparison.html', faculty_api_base_url=faculty_api_base_url, current_page="class-comparison")


    @app.route('/faculty/profile')
    @role_required('faculty')
    def facultyProfile():
        return render_template('faculty/profile.html', faculty_api_base_url=faculty_api_base_url, current_page="profile")


    @app.route('/faculty/change-password')
    @role_required('faculty')
    def facultyChangePassword():
        return render_template('faculty/change_password.html', faculty_api_base_url=faculty_api_base_url, current_page="change-password")


    # ========================================================================


    # ALL UNIVERSITY ADMIN ROUTES HERE
    @app.route('/university-admin')
    @preventAuthenticated
    def universityAdminLogin():
        return render_template('universityadmin/login.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url)


    @app.route('/university-admin/home')
    @role_required('universityAdmin')
    def universityAdminHome():
        return render_template('universityadmin/home.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url, current_page="home")


    @app.route('/university-admin/class-performance')
    @role_required('universityAdmin')
    def universityClassPerformance():
        return render_template('universityadmin/class-performance.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url, current_page="class-performance")


    @app.route('/university-admin/profile')
    @role_required('universityAdmin')
    def universityProfile():
        return render_template('universityadmin/profile.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url, current_page="profile")


    @app.route('/university-admin/change-password')
    @role_required('universityAdmin')
    def universityChangePassword():
        return render_template('universityadmin/change-password.html', university_admin_api_key=university_admin_api_key, university_admin_api_base_url=university_admin_api_base_url, current_page="change-password")


    # ========================================================================
    # Register the API blueprint
    app.register_blueprint(university_admin_api, url_prefix=university_admin_api_base_url)
    app.register_blueprint(faculty_api, url_prefix=faculty_api_base_url)
    app.register_blueprint(student_api, url_prefix=student_api_base_url)


    @app.route('/page_not_found')  # Define an actual route
    def page_not_found():
        return handle_404_error(None)


    @app.errorhandler(404)
    def handle_404_error(e):
        return render_template('404.html'), 404

    return app


    