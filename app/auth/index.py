from flask import (
    Blueprint,
    render_template,
    request,
    g,
    flash,
    session
)
from flask import current_app as app

import json
from functools import wraps
from datetime import datetime as dt
from datetime import timedelta

from app.scripts._global import (
    GLOBAL_CONFIG,
    selected_language
)
from app.scripts._cache import cache
from app.scripts.maproom_items import (
    load_maproom_items,
    load_navigation_items,
    load_maproom_page_text,
    _url_args_nav_path
)
from .scripts import *

auth = Blueprint(
    'auth', __name__,
    template_folder = 'templates',
    static_folder = 'static',
    static_url_path = '/static/auth'
)

pyText = auth_message_text()

def render_template_main(error_login):
    mapItems = load_maproom_items(None)
    mapNav = load_navigation_items(None)
    pageText = load_maproom_page_text(None, 'main')
    return render_template(
        'main.html',
        error_login=error_login,
        dataUser=g.dataUser,
        langUser=GLOBAL_CONFIG['language'],
        metInfo=GLOBAL_CONFIG['metInfo'],
        dataInfo=g.dataInfoCoverage,
        mapItems=mapItems,
        mapNav=mapNav,
        pageText=pageText,
        pageType='main',
        urlArgs=_url_args_nav_path(None)
    )

def render_template_user(user_page, dataUser):
    page_contorl = page_control_musers()
    mapNav = load_navigation_items([user_page])
    pageText = load_maproom_page_text(
        ['auth', user_page], 'user'
    )
    pageText['user_page'] = user_page
    return render_template(
        f'{user_page}.html',
        dataUser = dataUser,
        langUser=GLOBAL_CONFIG['language'],
        metInfo = GLOBAL_CONFIG['metInfo'],
        dataInfo=g.dataInfoCoverage,
        mapNav=mapNav,
        pageText=pageText,
        pageCtrl = page_contorl,
        pageType='user'
    )

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash(pyText['login0'], 'warning')
            g.dataUser = {'uid': -1}
            return render_template_main(True)

    return wrap

_dataUser = {}
@cache.cached(timeout=60, key_prefix='userlang_')
@auth.route('/set_languages_user')
def set_languages_user():
    lang_code = request.args.get('lang_code')
    selected_language(lang_code)
    user_page = request.args.get('user_page')
    return render_template_user(
        user_page, _dataUser[user_page]
    )

@auth.route('/users_management')
@login_required
def users_management():
    date = dt.today()
    date = date + timedelta(days=1)
    date = date.strftime('%Y-%m-%d')
    dataUser = {
        'fullname': '',
        'institution': '',
        'email': '',
        'username': '',
        'password': '',
        'role': 'user',
        'access': 'climatology',
        'expiry': date,
        'extract': ['mapmpoints'],
        'analysis': [],
        'uid': -1
    }
    _dataUser['users-management'] = dataUser

    return render_template_user('users-management', dataUser)

@auth.route('/user_account')
@cache.cached(timeout=60, key_prefix='user_')
@login_required
def user_account():
    username = session['data']['username']
    dataUser = getUserData(username)[0]
    for col in ['multipoints', 'shapefiles', 'geojson']:
        dataUser[col] = getFilesUserData(username, col)
    _dataUser['user-account'] = dataUser

    return render_template_user('user-account', dataUser)

@auth.route('/createUser', methods=['POST'])
@login_required
def createUser():
    dataUser = request.get_json()
    try:
        if dataUser['update']:
            out = editUser(dataUser)
        else:
            out = addUser(dataUser)
    except Exception as e:
        out = {'status': -1, 'message': str(e), 'code': 'error'}

    return json.dumps(out)

@auth.route('/deleteUser', methods=['POST'])
@login_required
def deleteUser():
    data = request.get_json()
    try:
        out = removeUser(data['uid'])
        return json.dumps(out)
    except Exception as e:
        return json.dumps({'message': str(e), 'code': 'error'})

@auth.route('/getUserList', methods = ['POST'])
@login_required
def getUserList():
    try:
        out = getAllUsersList()
        date = dt.today()
        date = date.strftime('%Y-%m-%d')
        return json.dumps({'status': 0, 'data': out, 'date': date})
    except Exception as e:
        return json.dumps({'status': -1, 'message': str(e)})

@auth.route('/getUserInfo')
@login_required
def getUserInfo():
    username = request.args.get('username')
    try:
        user = getUserData(username)[0]
        if user['fullname'] == 'null':
            msg = f'{pyText['login4']}: {username}'
            return json.dumps({'status': -1, 'message': msg})
        else:
            return json.dumps({'status': 0, 'data': user})
    except Exception as e:
        return json.dumps({'status': -1, 'message': str(e)})

@auth.route('/login', methods = ['POST'])
def loginUser():
    username = request.form['username']
    password = request.form['password']
    # remember = True if request.form.get('remember') else False
    session['logged_in'] = False
    g.dataUser = {'uid': -1}
    try:
        ret = loginProc(username, password)

        if ret['status'] == -1:
            flash(ret['message'], 'error')
            return render_template_main(True)
        else:
            flash(pyText['login1'], 'success')
            dataUser = ret['data']
            session['logged_in'] = True
            session['data'] = {
                'username': dataUser['username'],
                'expiry': dataUser['expiry'],
                'role': dataUser['role'],
                'access': dataUser['access'],
                'extract': dataUser['extract'],
                'analysis': dataUser['analysis'],
                'uid': dataUser['uid'],
                'api_key': dataUser['api_key']
            }
            g.dataUser = session['data']
            return render_template_main(False)
    except Exception as e:
        flash(str(e), 'error')
        return render_template_main(True)

@auth.route('/logout')
@login_required
def logoutUser():
    session['logged_in'] = False
    session.pop('data', None)
    session.clear()
    g.dataUser = {'uid': -1}
    flash(pyText['login2'], 'success')
    return render_template_main(False)

@auth.route('/new_api_key')
@login_required
def new_api_key():
    username = request.args.get('username')
    pyobj = sql_generateAPIKey(username)
    return json.dumps(pyobj)

@auth.route('/change_password', methods = ['POST'])
@login_required
def change_password():
    user = request.get_json()
    pyobj = changePassword(user)
    return json.dumps(pyobj)

@auth.route('/forgot_password')
def forgot_password():
    g.dataUser = {'uid': -1}
    flash(pyText['login3'], 'success')
    return render_template_main(False)

@auth.route('/upload_user_files', methods = ['POST'])
@login_required
def upload_user_files():
    username = session['data']['username']
    colname = request.form['colname']
    if colname == 'shapefiles':
        userfiles = request.files.getlist('filesUser')
    else:
        userfiles = request.files['filesUser']

    shp = colname == 'shapefiles'
    pyobj = saveUserUploadedFile(username, userfiles, colname, shp)
    return json.dumps(pyobj)

@auth.route('/delete_user_files')
@login_required
def delete_user_files():
    username = session['data']['username']
    userfile = request.args.get("file")
    colname = request.args.get("colname")
    shp = colname == 'shapefiles'
    pyobj = deleteUserSavedFile(username, userfile, colname, shp)
    return json.dumps(pyobj)
