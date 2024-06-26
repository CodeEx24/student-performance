
from flask import Flask, render_template, redirect, url_for, session
from flask_caching import Cache
from flask_cors import CORS
from Api.v1.student.api_routes import student_api
from Api.v1.faculty.api_routes import faculty_api
from Api.v1.universityadmin.api_routes import university_admin_api
from Api.v1.systemadmin.api_routes import system_admin_api
from Api.v1.registrar.api_routes import registrar_api
from oauth2 import config_oauth
from utils import getCurrentUser
import os
from dotenv import load_dotenv
from models import init_db
from decorators.auth_decorators import preventAuthenticated, role_required
from datetime import  timedelta
from mail import mail
from werkzeug.security import check_password_hash
from datetime import datetime


def create_app():
    load_dotenv()  # Load environment variables from .env file
    app = Flask(__name__)

    if __name__ == '__main__':
        app.run(debug=False)
    
    if os.getenv("CONFIG_MODE") == "production":
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("PRODUCTION_DATABASE_URI")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("PRODUCTION_DATABASE_URI")
        
    # Do not set this to 1 in production
    os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Configure Flask to use HTTPS
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # or 'Strict'
    app.config['SESSION_PERMANENT'] = True
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['OAUTH2_REFRESH_TOKEN_GENERATOR'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    app.secret_key = os.getenv('SECRET_KEY')
    Cache(app, config={'CACHE_TYPE': 'simple'})


    # Allowed third party apps
    allowed_origins = ["*"]
    CORS(app, origins=allowed_origins, allow_headers=["Authorization", "X-API-Key", "x-csrftoken"])

    # jwt = JWTManager(app)
    # oauth = OAuth2Provider(app)
    # talisman = Talisman(app)
    # csrf = CSRFProtect(app)
    init_db(app)
    
   
    # Configure Flask-Mail for sending emails
    app.config['MAIL_SERVER'] =  os.getenv("MAIL_SERVER")
    app.config['MAIL_PORT'] =  os.getenv("MAIL_PORT")
    app.config['MAIL_USERNAME'] =  os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    mail.init_app(app)

    # The api base url for api endpoints
    student_api_base_url = os.getenv("STUDENT_API_BASE_URL")
    faculty_api_base_url = os.getenv("FACULTY_API_BASE_URL")
    university_admin_api_base_url = os.getenv("UNIVERSITY_ADMIN_API_BASE_URL")
    system_admin_api_base_url = os.getenv("SYSTEM_ADMIN_API_BASE_URL")
    registrar_api_base_url = os.getenv("REGISTRAR_API_BASE_URL")

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
        # Check if there is user role
        if 'user_role' in session:
            role = session['user_role']
            return redirect(url_for(f"{role}Home"))
        return render_template('main/index.html')


    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('home'))

    # ========================================================================
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
    
    @app.route('/faculty/reset-request')
    @preventAuthenticated
    def facultyResetRequest():
        print("faculty_api_base_url: ", faculty_api_base_url)
        return render_template('faculty/reset_password_request.html', faculty_api_base_url=faculty_api_base_url)


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

    @app.route('/university-admin/reset-request')
    @preventAuthenticated
    def universityAdminResetRequest():
        print("university_admin_api_base_url: ", university_admin_api_base_url)
        return render_template('universityadmin/reset_password_request.html', university_admin_api_base_url=university_admin_api_base_url)


    @app.route('/university-admin/home')
    @role_required('universityAdmin')
    def universityAdminHome():
        # json_performance_data = getOverallCoursePerformance()
        # json_performance_data=json_performance_data.get_json()
        return render_template('universityadmin/home.html', university_admin_api_base_url=university_admin_api_base_url, current_page="home")
    

    @app.route('/university-admin/all/class')
    @role_required('universityAdmin')
    def universityAdminAllClass():
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
    def universityAdminProfile():
        universityAdmin = getCurrentUser('universityAdmin')
        return render_template('universityadmin/profile.html', university_admin_api_base_url=university_admin_api_base_url, current_page="profile", universityAdmin=universityAdmin.to_dict())


    @app.route('/university-admin/change-password')
    @role_required('universityAdmin')
    def universityAdminChangePassword():
        return render_template('universityadmin/change-password.html', university_admin_api_base_url=university_admin_api_base_url, current_page="change-password")
    
    
    @app.route('/university-admin/finalized-grades')
    @role_required('universityAdmin')
    def universityAdminFinalizedGrades():
        return render_template('universityadmin/finalized-grade2.html', university_admin_api_base_url=university_admin_api_base_url, current_page="finalized-grades")
    
    
    @app.route('/university-admin/honors-criteria')
    @role_required('universityAdmin')
    def universityAdminHonorsCriteria():
        return render_template('universityadmin/honors-criteria.html', university_admin_api_base_url=university_admin_api_base_url, current_page="honors-criteria")
    
    
    @app.route('/university-admin/student-lister')
    @role_required('universityAdmin')
    def universityAdminStudentLister():
        return render_template('universityadmin/student-lister.html', university_admin_api_base_url=university_admin_api_base_url, current_page="student-lister")
    
    
    @app.route('/university-admin/student-achievements')
    @role_required('universityAdmin')
    def universityAdminStudentAchievements():
        return render_template('universityadmin/achievement.html', university_admin_api_base_url=university_admin_api_base_url, current_page="student-achievements")
    
    
    @app.route('/university-admin/latin-honors')
    @role_required('universityAdmin')
    def universityAdminLatinHonors():
        return render_template('universityadmin/latin-honors.html', university_admin_api_base_url=university_admin_api_base_url, current_page="latin-honors")




    # ========================================================================
    # ALL REGISTRAR ROUTES HERE
    @app.route('/registrar')
    @preventAuthenticated
    def registrarLogin():
        return render_template('registrar/login.html')

    @app.route('/registrar/reset-request')
    @preventAuthenticated
    def registrarResetRequest():
        print("registrar_api_base_url: ", registrar_api_base_url)
        return render_template('registrar/reset_password_request.html', registrar_api_base_url=registrar_api_base_url)

    @app.route('/registrar/home')
    @role_required('registrar')
    def registrarHome():
        return render_template('registrar/home.html', registrar_api_base_url=registrar_api_base_url, current_page="home")
    
    @app.route('/registrar/students')
    @role_required('registrar')
    def registrarStudents():
        return render_template('registrar/students.html', registrar_api_base_url=registrar_api_base_url, current_page="students")
    
    @app.route('/registrar/student-requirements')
    @role_required('registrar')
    def registrarStudentRequirements():
        return render_template('registrar/student-requirements.html', registrar_api_base_url=registrar_api_base_url, current_page="student-requirements")
    
    
    @app.route('/registrar/profile')
    @role_required('registrar')
    def registrarProfile():
        registrar = getCurrentUser('registrar')
        return render_template('registrar/profile.html', registrar_api_base_url=registrar_api_base_url, current_page="profile", registrar=registrar.to_dict())
    
    
    @app.route('/registrar/change-password')
    @role_required('registrar')
    def registrarChangePassword():
        return render_template('registrar/change-password.html', registrar_api_base_url=registrar_api_base_url, current_page="change-password")


    # ========================================================================
    # ALL SYSTEM ADMIN ROUTES HERE
    @app.route('/system-admin')
    @preventAuthenticated
    def systemAdminLogin():
        return render_template('systemadmin/login.html')

    @app.route('/system-admin/reset-request')
    @preventAuthenticated
    def systemAdminResetRequest():
        print("system_admin_api_base_url: ", system_admin_api_base_url)
        return render_template('systemadmin/reset_password_request.html', system_admin_api_base_url=system_admin_api_base_url)


    @app.route('/system-admin/home')
    @role_required('systemAdmin')
    def systemAdminHome():
        return render_template('systemadmin/home.html', system_admin_api_base_url=system_admin_api_base_url, current_page="home")
    
    @app.route('/system-admin/clients')
    @role_required('systemAdmin')
    def systemAdminClients():
        return render_template('systemadmin/clients.html', system_admin_api_base_url=system_admin_api_base_url, current_page="clients")
    
    @app.route('/system-admin/grades')
    @role_required('systemAdmin')
    def systemAdminGrades():
        return render_template('systemadmin/grades.html', system_admin_api_base_url=system_admin_api_base_url, current_page="grades")
    
    
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
    app.register_blueprint(registrar_api, url_prefix=registrar_api_base_url)



    @app.route('/page_not_found')  # Define an actual route
    def page_not_found():
        return handle_404_error(None)


    @app.errorhandler(404)
    def handle_404_error(e):
        return render_template('404.html'), 404

    return app


    