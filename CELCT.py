import os, os.path
import pymysql as mysql
import sqlite3 as sqlite
import json, yaml
import string, random

lwc_to_locker_protectables = {54:1, 61:1, 62:1, 23:1, 64:2, 71:2, 96:2, 107:2, 0:3}
lwc_to_locker_types = {0:1, 1:2, 2:1}

class Protection(object):
    ''' A protection
    '''
    x = 0
    y = 0
    z = 0
    world = 'world'
    owner = 'user'
    drop_transfer = 0
    password = ''
    # id of type of thing that is protected
    protected_type = 0
    # type of protection
    protection_type = 0
    # {'totokaka':3} Bitmasked. 1<<0, 1<<1, 1<<2; Put items, take items, manage access's
    invited_users = {}

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
        
    def get_protections(self, conn):
        print("This should not happen")
    
class LWC(Plugin):
    ''' LWC
    '''
    name = 'LWC'
    
    def is_config_folder(self, folder):
        return folder == self.name
    
    def find_connection_details(self):
        config = yaml.load(open('./LWC/core.yml').read())['database']
        self.adapter = config['adapter']
        self.path = config['path'].replace('plugins', '.')
        self.host = config['host']
        self.port = 3306
        if ':' in self.host:
            split = self.host.split(':')
            self.port = int(split[1])
            self.host = split[0]
        self.database = config['database']
        self.username = config['username']
        self.password = config['password']
        self.prefix = config['prefix']
        
    def get_connection(self):
        if self.adapter == 'mysql':
            conn = mysql.connect(host=self.host, port=self.port, user=self.username, passwd=self.password, db=self.database)
            cur = conn.cursor()
            cur.execute('SHOW TABLES')
            rows = cur.fetchall()
            if ('{}protections'.format(self.prefix),) not in rows:
                raise Exception("LWC's database does not contain the protections table!")
            cur.close()
            return conn
        if self.adapter == 'sqlite':
            conn = sqlite.connect(self.path)
            cur = conn.cursor()
            cur.execute('SELECT name FROM sqlite_master WHERE type=\'table\'')
            rows = cur.fetchall()
            if ('{}protections'.format(self.prefix),) not in rows:
                raise Exception("LWC's database does not contain the protections table!")
            cur.close()
            return conn
    
    def get_protections(self, conn):
        protections = set()
        cur = conn.cursor()
        cur.execute("SELECT (owner, type, x, y, z, data, blockId, world, password) FROM {prefix}protections".format(prefix=self.prefix))
        for (owner, protection_type, x, y, z, data, blockId, world) in cur:
            protection = Protection()
            protection.x = x
            protection.y = y
            protection.z = z
            protection.world = world
            protection.owner = owner
            if blockId in lwc_to_locker_protectables.keys():
                protection.protected_type = lwc_to_locker_protectables[blockId]
            else:
                protection.protected_type = lwc_to_locker_protectables[0]
            protection.protection_type = lwc_to_locer_types[protection_type]
            if not data == None:
                invited = json.loads(data).get('rights', None)
                for invite in invited:
                    name = invite['name']
                    rights = invite['rights']
                    if rights == 2:
                        rights = 1<<0|1<<1|1<<2
                    else:
                        rights = 1<<0|1<<1
                    protection.invited_users[name] = rights
            protection.password = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(4))
            protections.add(protection)
        cur.close()
                    
        return protections;
    
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
        protections.update(plugin.get_protections(conn))
        print('DONE')
    return protections
    
def insert_protections(protections):
    print('==> Copying protections to Locker')
    print('    ==> ', end='')
    cur = conn.cursor()
    for protection in protections:
        try:
            cur.execute("INSERT INTO {prefix}locks (owner_id, type, lock_type, password, droptransfer) VALUES ((SELECT `key` FROM `{prefix}user` WHERE player='{a}'),{b},{c},'{d}', {e})"\
                        .format(a=protection.owner, b=protection.protected_type, c=protection.protection_type, d=protection.password, e=protection.drop_transfer, prefix=db_tableprefix))
            for user, access in protection.invited_users.items():
                cur.execute("INSERT INTO {prefix}lockaccesslist (user_id, lock_id, level) VALUES ((SELECT `key` FROM `{prefix}user` WHERE player='{a}'),{b},{c})"\
                            .format(a=user, b=cur.lastrowid, c=access))
        except Exception:
            print('Failed to insert a home')
            print('    ==> ', end='')
    cur.close()
    print('DONE')
    
def main():
    plugins = {'LWC': LWC()}
    available_plugins = set()
    
    print('''=============== CubeEngine Locker Conversion Tool ================
Welcome to CubeEngine Locker Conversion Tool, CELCT for short. This tool will 
autmatically detect what protect plugins you have installed and move
the protections from them to Locker.''');
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
