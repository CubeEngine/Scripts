import os, os.path
import pymysql as mysql
import sqlite3 as sqlite

class Plugin(object):
    ''' A class to represent a plugin which can be converted to CE Protect with this tool
    '''
    # The name of the plugin
    name = None
            
    def is_config_folder(self, folder):
        print("This should not happen")
        
    def find_connection_details(self):
        print("This should not happen")
        
    def get_connection(self):
        print("This should not happen")
        
    def get_protections(self):
        print("This should not happen")
    
class LWC(Plugin):
    ''' LWC
    '''
    name = 'LWC'
    
    def is_config_folder(self, folder):
        return folder == self.name
    
    def find_connection_details(self):
        pass # TODO
    
    def get_connection(self):
        return None # TODO
    
    def get_protections(self):
        return set() # TODO
    
def is_ce_present():
    return os.path.exists('./CubeEngine/') and os.path.exists('./CubeEngine/database.yml') \
            and os.path.isfile('./CubeEngine/database.yml')
    
def check_workspace():
    print('==> Checking workspace')
    print('    ==> ', end='')
    if not is_ce_present():
        print('FAIL')
        print('    ==> It looks like cubeengine is not installed')
        exit(1)
    else:
        print('OK')

def get_ce_db_info():
    print('==> Gathering database connection info for CubeEngine')
    print('    ==> ', end='')
    global db_hostname, db_port, db_name, db_user, db_pass, db_tableprefix
    config = yaml.load(open('./CubeEngine/database.yml').read())
    print('Found connection info')
    print('    ==> ', end='')
    global conn
    conn = mysql.connect(host=config['host'], port=config['port'], user=config['user'], passwd=config['password'], db=config['database'])
    cur = conn.cursor()
    cur.execute('SHOW TABLES')
    cur.close()
    print('Connected')
    print('    ==> OK')

def get_available_plugins(plugins):
    print('==> Finding other protection plugins')
    available_plugins = set()
    for folder in [f for f in os.listdir('.') if os.path.isdir(f)]:
        for plugin in plugins.values():
            if plugin.is_config_folder(folder):
                available_plugins.add(plugin)
                print('    ==> Found {}'.format(plugin.name))
                break
    if len(available_plugins) < 1:
        print('    ==> No plugins found!')
        exit(1)
    return available_plugins

def get_db_connections_plugins(available_plugins):
    print('==> Gathering database connection info from plugins')
    connections = dict()
    for plugin in available_plugins:
        print('    ==> {}'.format(plugin.name))
        try:
            plugin.find_connection_details()
            print('        ==> Found connection info')
            conn = plugin.get_connection()
            print('        ==> Connected')
            connections[plugin] = conn
            print('        ==> OK')
        except Exception as ex:
            print('        ==> FAIL')
            raise ex
            exit(2)
    return connections
            
def get_protections(connections):
    print('==> Copying Protections into memory from the databases')
    protections = set()
    for plugin in connections.keys():
        print('    ==> From {}'.format(plugin.name))
        print('        ==>', end='')
        conn = connections[plugin]
        protections.update(plugin.get_protections())
        print('DONE')
    return protections
    
def insert_protections(protections):
    print('==> Copying protections to BaumGuard')
    # TODO
    print('    ==> DONE')
    
def main():
    plugins = {'LWC': LWC()}
    available_plugins = set()
    
    print('''=============== CubeEngine BaumGuard Conversion Tool ================
Welcome to CubeEngine BaumGuard Conversion Tool. This tool will 
autmatically detect what protect plugins you have installed and move
the conversions from them to BaumGuard.''');
    input()
    
    check_workspace()
    get_ce_db_info()
    available_plugins = get_available_plugins(plugins)
    database_connections = get_db_connections_plugins(available_plugins)
    protections = get_protections(database_connections)
    insert_protections(protections)
    
    print('==> DONE')
    print('    ==> Converted {} protections'.format(len(protections)))
    
        
if __name__ == "__main__":
	main()
