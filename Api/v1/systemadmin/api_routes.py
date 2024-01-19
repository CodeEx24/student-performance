# api/api_routes.py
from flask import Blueprint, jsonify, request, redirect, url_for, flash, session, render_template
from models import SystemAdmin, OAuth2Client, db, Student, OAuth2Token
from authlib.oauth2 import OAuth2Error

from werkzeug.security import check_password_hash
from decorators.auth_decorators import role_required
import time
from werkzeug.security import gen_salt
from oauth2 import authorization

import os

system_admin_api = Blueprint('system_admin_api', __name__)


def current_user():
    if 'id' in session:
        uid = session['id']
        return SystemAdmin.query.get(uid)
    return None

# Login
@system_admin_api.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(email)
        user = SystemAdmin.query.filter_by(Email=email).first()
        print('user: ', user)
        # Check for password
        if user and check_password_hash(user.Password, password):
            session['id'] = user.SysAdminId
            session['user_role'] = 'systemAdmin'
            user = current_user()
            print('session: ', session)
            return jsonify({"success": True, "message": "Login successful"}), 200
        else:
            return jsonify({"error": False, "message": "Invalid email or password"}), 401

# Make a client list route
@system_admin_api.route('/clients', methods=['GET'])
def clients():
    user = current_user()
    if user:
        # Get all clients list
        clients = OAuth2Client.query.all()
        list_client = []
        for client in clients:
            print(client.client_metadata)
            list_client.append({"metadata": client.client_metadata, 'client_id': client.client_id, 'client_secret': client.client_secret})
            
        if clients:
            return jsonify(list_client)
        else:
            return jsonify({"message": "No clients found"}), 404
    else:
        clients = []
    return jsonify({"message": "No clients found"}), 404


    
    
    
    # Check if token
    # token = authorization.create_token_response()
    # print(token)
    # return token


@system_admin_api.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    # if user log status is not true (Auth server), then to log it in
    if not user:
        return redirect(url_for('home.home', next=request.url))
    if request.method == 'GET':
        try:
            grant = authorization.get_consent_grant(end_user=user)
        except OAuth2Error as error:
            return error.error
        return render_template('authorize.html', user=user, grant=grant)
    if not user and 'email' in request.form:
        email = request.form.get('email')
        user = SystemAdmin.query.filter_by(Email=email).first()
    if request.form['confirm']:
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


@system_admin_api.route('/create_client', methods=('GET', 'POST'))
def createClient():
    user = current_user()
    if not user:
        return redirect(url_for('systemAdminLogin'))
    if request.method == 'GET':
        return render_template('create_client.html')

    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.SysAdminId,
    )

    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    client.set_client_metadata(client_metadata)

    if form['token_endpoint_auth_method'] == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)

    db.session.add(client)
    db.session.commit()
    return redirect(url_for('systemAdminClients'))
    
    
# Create token checker
    
@system_admin_api.route('/login2', methods=['POST'])
def login2():
    print("CHECKING SYSTEM LOGIN")
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print("CHECKING SYSTEM LOGIN")
        systemAdmin = SystemAdmin.query.filter_by(Email=email).first()
        if systemAdmin and check_password_hash(systemAdmin.Password, password):
            session['user_id'] = systemAdmin.SysAdminId
            session['user_role'] = 'systemAdmin'
            print("SUCCESSFUL LOGIN")
            return redirect(url_for('systemAdminHome'))
        else:
            flash('Invalid email or password', 'danger')
            print("FAILED LOGIN")
            return redirect(url_for('systemAdminLogin'))
    return redirect(url_for('systemAdminLogin'))


@system_admin_api.route('/ads', methods=['GET'])
def helo():
    print("CHECKING SYSTEM LOGIN")
    return ({"message": " HELLO THERE FROM RTHIS"})
