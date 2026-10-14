import os
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.util import load_yaml_file
from app.scripts.maproom_items import parse_lang_yaml_nested

def page_control_admin(admin_page):
    dir_app = GLOBAL_CONFIG['app_dir']
    dir_yaml = os.path.join(dir_app, 'admin', 'yaml')
    yaml_file = os.path.join(dir_yaml, f'{admin_page}.yaml')
    yaml_tmp = load_yaml_file(yaml_file)
    return parse_lang_yaml_nested(yaml_tmp)
