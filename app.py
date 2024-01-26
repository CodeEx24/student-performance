
from flask import Flask, render_template, redirect, url_for, session
from flask_caching import Cache
from flask_cors import CORS

from Api.v1.student.api_routes import student_api
from Api.v1.faculty.api_routes import faculty_api
from Api.v1.universityadmin.api_routes import university_admin_api
from Api.v1.systemadmin.api_routes import system_admin_api
from oauth2 import config_oauth

from utils import getOverallCoursePerformance, getCurrentUser

# from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

from models import init_db
# from flask_jwt_extended import JWTManager

from decorators.auth_decorators import preventAuthenticated, role_required

from datetime import  timedelta
from mail import mail  # Import mail from the mail.py module
# from flask_oauthlib.provider import OAuth2Provider
from werkzeug.security import check_password_hash
# Get models OAuth2Client
# from models import OAuth2Client, Student, OAuth2Token
# from flask_talisman import Talisman
# from flask_wtf.csrf import CSRFProtect
from datetime import datetime


def create_app():
    load_dotenv()  # Load environment variables from .env file
    app = Flask(__name__)

    # talisman = Talisman(app)
    # csrf = CSRFProtect(app)


    if __name__ == '__main__':
        app.run(debug=False)
    
    # SETUP YOUR POSTGRE DATABASE HERE
    # Check if CONFIG_MODE is set to development
    if os.getenv("CONFIG_MODE") == "production":
        print("USING PRODUCTION")
        # Set the value to DEVELOPMENT_DATABASE_URI
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('PRODUCTION_DATABASE_URI')
    else:
        print("USING DEVELOPMENT")
        # Set the value to the default DATABASE_URI
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://pupqc_cloud_user:1r7kf1cJ41wPBAfm88mF77LJNIUuW9jG@dpg-cme4jv6n7f5s73f44qi0-a.singapore-postgres.render.com/pupqc_cloud'
        
    # Do not set this to 1 in production
    os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Configure Flask to use HTTPS
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # or 'Strict'
    app.config['SESSION_PERMANENT'] = True
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['OAUTH2_REFRESH_TOKEN_GENERATOR'] = True
    # app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Replace 'your-secret-key' with an actual secret key
    app.secret_key = os.getenv('SECRET_KEY')
    Cache(app, config={'CACHE_TYPE': 'simple'})
    # cache.init_app(app)

    # Allowed third party apps
    allowed_origins = ["*"]
    CORS(app, origins=allowed_origins, allow_headers=["Authorization", "X-API-Key"])

    # jwt = JWTManager(app)
    init_db(app)
    # oauth = OAuth2Provider(app)
   
    # Configure Flask-Mail for sending emails
    app.config['MAIL_SERVER'] =  os.getenv("MAIL_SERVER")
    app.config['MAIL_PORT'] =  os.getenv("MAIL_PORT")
    app.config['MAIL_USERNAME'] =  os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    # app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    mail.init_app(app)
    # The Api Key is static for development mode. The Api key in future must refresh in order to secure the api endpoint of the application
    # student_api_key = os.getenv('STUDENT_API_KEY')
    # faculty_api_key = os.getenv('FACULTY_API_KEY')
    # university_admin_api_key = os.getenv('UNIVERSITY_ADMIN_API_KEY')
    # system_admin_api_key = os.getenv('SYSTEM_ADMIN_API_KEY')

    # The api base url for api endpoints
    student_api_base_url = os.getenv("STUDENT_API_BASE_URL")
    faculty_api_base_url = os.getenv("FACULTY_API_BASE_URL")
    university_admin_api_base_url = os.getenv("UNIVERSITY_ADMIN_API_BASE_URL")
    system_admin_api_base_url = os.getenv("SYSTEM_ADMIN_API_BASE_URL")

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




    @app.route('/practice')
    def practice():
        return render_template('practice.html')



    @app.route('/')
    @preventAuthenticated
    def home():
        return render_template('main/index.html')


    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('home'))  # Redirect to home or appropriate route

    # ========================================================================


    # ALL STUDENT ROUTES HERE
    # ALL STUDENT ROUTES HERE
    @app.route('/student')
    @preventAuthenticated
    def studentLogin():
        return render_template('student/login.html')
    
    @app.route('/student/otp')
    @preventAuthenticated
    def studentOtp():
        # Check if user_id exist and otp
        if 'user_id' in session and 'otp' in session:
            # Check if otp_expired_at already expired
            if session['otp_expired_at'] < datetime.now():
                session.clear()
                return handle_404_error(None)
            else:
                return render_template('student/login_otp.html')
        else:
            session.clear()
            # Return 404
            return handle_404_error(None)
        
    

    @app.route('/student/reset-request')
    @preventAuthenticated
    def studentResetRequest():
        return render_template('student/reset_password_request.html', student_api_base_url=student_api_base_url)


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
        student = getCurrentUser('student')
        return render_template('student/profile.html', student_api_base_url=student_api_base_url, current_page="profile", student=student.to_dict())


    @app.route('/student/change-password')
    @role_required('student')
    def changePassword():
        student = getCurrentUser('student')
        return render_template('student/change_password.html', student_api_base_url=student_api_base_url,  current_page="change-password", student=student.to_dict())


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
    
    @app.route('/faculty/practice')
    @role_required('faculty')
    def facultyPractice():
        return render_template('faculty/practice.html', faculty_api_base_url=faculty_api_base_url, current_page="dashboard")


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
        faculty = getCurrentUser('faculty')
        return render_template('faculty/profile.html', faculty_api_base_url=faculty_api_base_url, current_page="profile", faculty=faculty.to_dict())


    @app.route('/faculty/change-password')
    @role_required('faculty')
    def facultyChangePassword():
        return render_template('faculty/change_password.html', faculty_api_base_url=faculty_api_base_url, current_page="change-password")


    # ========================================================================
    # ALL UNIVERSITY ADMIN ROUTES HERE
    @app.route('/university-admin')
    @preventAuthenticated
    def universityAdminLogin():
        return render_template('universityadmin/login.html', university_admin_api_base_url=university_admin_api_base_url)


    @app.route('/university-admin/home')
    @role_required('universityAdmin')
    def universityAdminHome():
        # json_performance_data = getOverallCoursePerformance()
        # json_performance_data=json_performance_data.get_json()
        return render_template('universityadmin/home.html', university_admin_api_base_url=university_admin_api_base_url, current_page="home")
    
    @app.route('/university-admin/students')
    @role_required('universityAdmin')
    def universityAdminStudents():
        return render_template('universityadmin/students.html', university_admin_api_base_url=university_admin_api_base_url, current_page="students")


    @app.route('/university-admin/all/class')
    @role_required('universityAdmin')
    def universityAllClass():
        return render_template('universityadmin/all-class.html', university_admin_api_base_url=university_admin_api_base_url, current_page="class-performance")
    
    @app.route('/university-admin/grades')
    @role_required('universityAdmin')
    def universityAdminGrades():
        return render_template('universityadmin/grades.html', university_admin_api_base_url=university_admin_api_base_url, current_page="grades")
    
    @app.route('/university-admin/class/<int:class_id>')
    @role_required('universityAdmin')
    def universityClass(class_id):
        return render_template('universityadmin/class.html', university_admin_api_base_url=university_admin_api_base_url, current_page="class-performance", class_id=class_id)
    
            
    @app.route('/university-admin/class-subject')
    @role_required('universityAdmin')
    def universityClassSubject():
        return render_template('universityadmin/class-subject.html', university_admin_api_base_url=university_admin_api_base_url, current_page="class-subject")
    
    
    @app.route('/university-admin/curriculum')
    @role_required('universityAdmin')
    def universityAdminCurriculum():
        return render_template('universityadmin/curriculum.html', university_admin_api_base_url=university_admin_api_base_url, current_page="curriculum")


    @app.route('/university-admin/profile')
    @role_required('universityAdmin')
    def universityProfile():
        universityAdmin = getCurrentUser('universityAdmin')
        return render_template('universityadmin/profile.html', university_admin_api_base_url=university_admin_api_base_url, current_page="profile", universityAdmin=universityAdmin.to_dict())


    @app.route('/university-admin/change-password')
    @role_required('universityAdmin')
    def universityChangePassword():
        return render_template('universityadmin/change-password.html', university_admin_api_base_url=university_admin_api_base_url, current_page="change-password")
    
    
    # @app.route('/university-admin/finalized-grades')
    # @role_required('universityAdmin')
    # def universityFinalizedGrades():
    #     return render_template('universityadmin/finalized-grades.html', university_admin_api_base_url=university_admin_api_base_url, current_page="finalized-grades")
    
    @app.route('/university-admin/finalized-grades')
    @role_required('universityAdmin')
    def universityFinalizedGrades():
        return render_template('universityadmin/finalized-grade2.html', university_admin_api_base_url=university_admin_api_base_url, current_page="finalized-grades")

    # ========================================================================
    # ALL SYSTEM ADMIN ROUTES HERE
    @app.route('/system-admin')
    @preventAuthenticated
    def systemAdminLogin():
        return render_template('systemadmin/login.html')

    @app.route('/system-admin/home')
    @role_required('systemAdmin')
    def systemAdminHome():
        return render_template('systemadmin/home.html', system_admin_api_base_url=system_admin_api_base_url, current_page="home")
    
    @app.route('/system-admin/clients')
    @role_required('systemAdmin')
    def systemAdminClients():
        return render_template('systemadmin/clients.html', system_admin_api_base_url=system_admin_api_base_url, current_page="clients")
    
    
    @app.route('/system-admin/class')
    @role_required('systemAdmin')
    def systemAdminClass():
        return render_template('systemadmin/class.html', system_admin_api_base_url=system_admin_api_base_url, current_page="class")
    
    @app.route('/system-admin/batch')
    @role_required('systemAdmin')
    def systemAdminBatch():
        return render_template('systemadmin/batch.html', system_admin_api_base_url=system_admin_api_base_url, current_page="batch")

    @app.route('/system-admin/students')
    @role_required('systemAdmin')
    def systemAdminStudents():
        return render_template('systemadmin/students.html', system_admin_api_base_url=system_admin_api_base_url, current_page="students")
    
    
    @app.route('/system-admin/faculties')
    @role_required('systemAdmin')
    def systemAdminFaculties():
        return render_template('systemadmin/faculty.html', system_admin_api_base_url=system_admin_api_base_url, current_page="faculty")
    
    
    @app.route('/system-admin/profile')
    @role_required('systemAdmin')
    def systemAdminProfile():
        systemAdmin = getCurrentUser('systemAdmin')
        return render_template('systemadmin/profile.html', system_admin_api_base_url=system_admin_api_base_url, current_page="profile", systemAdmin=systemAdmin.to_dict())
    
    @app.route('/system-admin/change-password')
    @role_required('systemAdmin')
    def systemAdminChangePassword():
        return render_template('systemadmin/change-password.html', system_admin_api_base_url=system_admin_api_base_url, current_page="change-password")
    
    # ========================================================================
    # Register the API blueprint
    config_oauth(app)
    app.register_blueprint(university_admin_api, url_prefix=university_admin_api_base_url)
    app.register_blueprint(system_admin_api, url_prefix=system_admin_api_base_url)

    app.register_blueprint(faculty_api, url_prefix=faculty_api_base_url)
    app.register_blueprint(student_api, url_prefix=student_api_base_url)



    @app.route('/page_not_found')  # Define an actual route
    def page_not_found():
        return handle_404_error(None)


    @app.errorhandler(404)
    def handle_404_error(e):
        return render_template('404.html'), 404

    return app


    