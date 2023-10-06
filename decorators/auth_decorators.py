from functools import wraps

from functools import wraps
from flask import redirect, url_for, session, render_template

def studentRequired(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_role' in session and session['user_role'] == 'student':
            return fn(*args, **kwargs)
        else:
            return render_template('404.html'), 404
    return wrapper


def facultyRequired(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_role' in session and session['user_role'] == 'faculty':
            return fn(*args, **kwargs)
        else:
            return render_template('404.html'), 404
    return wrapper


def universityAdminRequired(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_role' in session and session['user_role'] == 'universityAdmin':
            return fn(*args, **kwargs)
        else:
            return render_template('404.html'), 404
    return wrapper


def preventAuthenticated(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_role' in session:
            role = session['user_role']
            return redirect(url_for(f"{role}Home"))
        return fn(*args, **kwargs)
    return wrapper


# SERVER REQUIRED:
def role_required(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = session.get('user_role')
            if user_role == required_role:
                return func(*args, **kwargs)
            else:
                return render_template('404.html'), 404
        return wrapper
    return decorator

# def faculty_required(route_function):
#     @login_required
#     @wraps(route_function)
#     def wrapper(*args, **kwargs):
#         if current_user.is_authenticated and isinstance(current_user, Faculty):
#             return route_function(*args, **kwargs)
#         else:
#             abort(401)  # Unauthorized
#     return wrapper
