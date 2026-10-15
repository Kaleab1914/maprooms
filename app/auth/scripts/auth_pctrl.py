import os
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.util import load_yaml_file
from app.scripts.maproom_items import parse_lang_yaml_nested

def page_control_musers():
    dir_app = GLOBAL_CONFIG['app_dir']
    dir_yaml = os.path.join(dir_app, 'auth', 'yaml')
    yaml_file = os.path.join(dir_yaml, 'user-creation.yaml')
    yaml_tmp = load_yaml_file(yaml_file)
    page_contorl = parse_lang_yaml_nested(yaml_tmp)
    extract_file = os.path.join(dir_yaml, 'extraction-support.yaml')
    extract_tmp = load_yaml_file(extract_file)
    page_contorl.update(parse_lang_yaml_nested(extract_tmp))
    analysis_file = os.path.join(dir_yaml, 'download-analysis.yaml')
    analysis = load_yaml_file(analysis_file)
    page_contorl.update(parse_lang_yaml_nested(analysis))
    return page_contorl

def auth_message_text():
    dir_app = GLOBAL_CONFIG['app_dir']
    dir_yaml = os.path.join(dir_app, 'auth', 'yaml')
    py_file = os.path.join(dir_yaml, 'py-text.yaml')
    tmp = load_yaml_file(py_file)
    return parse_lang_yaml_nested(tmp)

def _get_admin_datauser():
    admin = {}
    admin['fullname'] = 'Maprooms Administrator'
    admin['institution'] = 'NMHS'
    admin['email'] = 'adminMaprooms@localhost'
    admin['username'] = 'admin'
    admin['password'] = 'admin'
    admin['role'] = 'admin'
    admin['access'] = 'all'
    admin['expiry'] = '2100-01-01'
    pgc = page_control_musers()
    admin['extract'] = list(pgc['extraction_support'].keys())
    admin['analysis'] = list(pgc['analysis'].keys())
    return {'status': 0, 'user': admin}

def _create_maproom_datauser():
    user = _get_admin_datauser()['user']
    user['role'] = 'user'
    user['username'] = 'maproom'
    user['fullname'] = 'Maproom'
    return user
