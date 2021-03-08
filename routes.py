import sqlalchemy

from config import loginManager, connex_app, app, db
from models import User, Request
from flask import render_template, jsonify, abort, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import func
import analysis


@connex_app.route('/')
@login_required
def home_page():
    return render_template('home.html')


@connex_app.route('/login')
def login_page():
    return render_template('login.html')


@connex_app.route('/index')
@login_required
def index_page():
    return render_template('index.html')


def login(logindata):
    login_ = logindata.get('login')
    password = logindata.get('password')

    if current_user.is_authenticated:
        abort(400, "User was already logged in")

    if login_ and password:
        user = User.query.filter_by(login=login_).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return make_response("Successfully logged in", 200)
        else:
            abort(400, "Login or password is not correct")
    else:
        abort(400, "Please fill login and password fields")
    return


@login_required
def logout():
    logout_user()
    return make_response("Successfully logged out", 200)


@login_required
def register(user_data):
    login_ = user_data.get('login')
    password = user_data.get('password')
    role = user_data.get('role')
    hash = generate_password_hash(password)
    id = db.session.query(func.count(User.id)).scalar() + 1

    user = User(id=id, login=login_, password=hash, role=role)
    db.session.add(user)
    db.session.commit()
    return make_response("Successfully registered person", 200)


@login_required
def execute_request(request_data):
    request_args = request_data.get('args_arr')
    request_args = request_args.split(",")
    user = User.query.filter_by(id=current_user.id).first()
    role = user.role_u

    if request_data.get('request_name') not in role.permissions:
        abort("Do not have permission", 400)
        return

    req = Request.query.filter_by(name=request_data.get('request_name')).first()
    req_text = req.text

    req_text = req_text.replace("%i", "{}")
    req_text = req_text.replace("%s", "'{}'")
    req_text = req_text.format(*request_args)

    req_result = db.session.execute(req_text)

    try:
        req_result_json = [dict(row.items()) for row in req_result]
        req_result_json = jsonify(req_result_json)
        db.session.commit()
        return make_response(req_result_json, 200)
    except sqlalchemy.exc.ResourceClosedError:
        db.session.commit()
        return make_response("Successfully executed request", 200)


@login_required
def get_all_requests():
    req_result = Request.query.all()
    result = []

    for row in req_result:
        if row.name in current_user.role_u.permissions:
            result.append({row.name: row.text})

    return make_response(jsonify(result), 200)


@login_required
def predict(predict_data):
    machine = predict_data.get('machineId')
    first_date = predict_data.get('first_date')
    last_date = predict_data.get('last_date')

    analysis.predict(machine, first_date, last_date)
    return make_response("Successfully predicted on given period", 200)


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        abort(400, "User need to be logged in before access")
    if response.status_code == 405:
        print(response)
    return response


@loginManager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
