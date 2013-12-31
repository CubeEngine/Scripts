# General imports:
import os, os.path, math
# Databases:
import pymysql as mysql
import sqlite3 as sqlite
# Parsing from configs, and data fields in databases:
import json, yaml
# Generating Random four digit password:
import string, random

# Dictionaries that maps from LWC's protection types to Locker's
lwc_to_locker_protectables = {23:1, 54:1, 61:1, 62:1, 23:1, 64:2, 71:2, 96:2, 107:2, 117:1, 146:1, 154:1, 158:1, 0:3}
lwc_to_locker_types = {0:2, 1:1, 2:1}

# SQL expressions for CubeEngine
sql_expressions = {
    'get_tables':
        '''SHOW TABLES
        ''',
    'insert_lock':
        '''INSERT INTO {prefix}locks
                       (owner_id
                       ,type
                       ,lock_type
                       ,password
                       ,last_access
                       ,created)
           VALUES      ((SELECT `key`
                         FROM   `{prefix}user`
                         WHERE  `player`= '{a}'
                         ORDER BY `key` ASC
                         LIMIT 1)
                       ,{b}
                       ,{c}
                       ,'{d}'
                       ,'{f}'
                       ,'{f}')
        ''',
    'insert_locklocation':
        '''INSERT INTO {prefix}locklocation 
                       (world_id
                       ,x
                       ,y
                       ,z
                       ,chunkX
                       ,chunkZ
                       ,lock_id)
           VALUES      ((SELECT `key`
                         FROM   `{prefix}worlds`
                         WHERE  `worldName`= '{a}'
                         ORDER BY `key` ASC
                         LIMIT 1)
                       ,{x}
                       ,{y}
                       ,{z}
                       ,{cx}
                       ,{cz}
                       ,{b})
        ''',
    'insert_lockaccesslist':
        '''INSERT INTO {prefix}lockaccesslist
                       (user_id
                       ,lock_id
                       ,level)
           VALUES      ((SELECT `key`
                         FROM   `{prefix}user`
                         WHERE  `player`= '{a}'
                         ORDER BY `key` ASC
                         LIMIT 1)
                       ,{b}
                       ,{c})
        ''',
    'find_without_location':
        '''SELECT {prefix}locks.id
           FROM   {prefix}locks
                  LEFT OUTER JOIN {prefix}locklocation
                               ON {prefix}locks.id = {prefix}locklocation.lock_id
           WHERE  {prefix}locklocation.id IS null
        ''',
    'delete_lock':
        '''DELETE FROM {prefix}locks
           WHERE  id={a}
        '''}

# Classes:

class Protection(object):
    ''' A protection
    Everything should be in Locker's format
    '''
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.world = 'world'
        self.owner = 'user'
        self.password = ''
        self.protected_type = 0
        self.protection_type = 0
        self.invited_users = {}

class Plugin(object):
    ''' A class to represent a plugin which has protections that can be converted to 
    CE Lock with this tool
    '''
    # The name of the plugin
    name = None
            
    def is_config_folder(self, folder):
        ''' Check if the supplied folder is the config folder of this plugin
        This is used to determine if the plugin is available
        Returns a bool
        '''
        pass
        
    def find_connection_details(self):
        ''' Get ready the connection details
        Doesn't return anything
        '''
        pass
        
    def get_connection(self):
        ''' Connect to the database and return the connection
        The connection should be tested.
        Returns a Connection object
        '''
        pass
        
    def get_protections(self, conn):
        ''' Get all protections this plugin has in it's database
        Returns a set of Protection objects
        '''
        pass
    
class LWC(Plugin):
    ''' LWC
    '''
    name = 'LWC'
    prefix = 'lwc_'
    sql_expressions = {
        'get_tables_mysql':
            '''SHOW TABLES
            ''',
        'get_tables_sqlite':
            '''SELECT name 
               FROM   sqlite_master 
               WHERE  type='table'
            ''',
        'get_protection':
            '''SELECT owner,
                      type,
                      x,
                      y,
                      z,
                      data,
                      blockid,
                      world
               FROM   lwc_protections
               WHERE  1
            '''}
    
    def __init__(self):
        self.name = LWC.name
        self.prefix = LWC.prefix
        
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
            conn = mysql.connect(host=self.host, port=self.port, user=self.username, 
                                 passwd=self.password, db=self.database)
            cur = conn.cursor()
            cur.execute(LWC.sql_expressions['get_tables_mysql'])
            rows = cur.fetchall()
            if ('{}protections'.format(self.prefix),) not in rows:
                raise Exception("LWC's database does not contain the protections table!")
            cur.close()
            return conn
        if self.adapter == 'sqlite':
            conn = sqlite.connect(self.path)
            cur = conn.cursor()
            cur.execute(LWC.sql_expressions['get_tables_sqlite'])
            rows = cur.fetchall()
            if ('{}protections'.format(self.prefix),) not in rows:
                raise Exception("LWC's database does not contain the protections table!")
            cur.close()
            return conn
    
    def get_protections(self, conn):
        protections = set()
        cur = conn.cursor()
        cur.execute(LWC.sql_expressions['get_protection'].format(prefix=self.prefix))
        for owner, protection_type, x, y, z, data, blockId, world in cur:
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
            protection.protection_type = lwc_to_locker_types[protection_type]
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
            protection.password = random_password() 
            protections.add(protection)
        cur.close()
                    
        return protections;
    
# Util functions

def random_password():
    ''' Generate a random password
    The password will consist of lowercase letters and digits, and be
    4 characters long.
    Returns a String
    '''
    return ''.join(random.choice(string.ascii_lowercase + string.digits)\
                   for x in range(4))
    
# The functions that check and fetch info    
    
def check_workspace():
    ''' Check if the workspace is correct
    This will check if CubeEngine is installed, by checking for the
    database.yml file in the CubeEngine folder
    returns a bool
    '''
    print('==> Checking workspace')
    print('    ==> ', end='')
    if not (os.path.exists('./CubeEngine/') and 
            os.path.exists('./CubeEngine/database.yml') and 
            os.path.isfile('./CubeEngine/database.yml')):
        print('FAIL')
        print('    ==> It looks like cubeengine is not installed')
        exit(1)
    else:
        print('OK')

def get_ce_db_info():
    ''' Get the database connection info for CubeEngine
    The values will be placed in the global fields:
    db_hostname, db_port, db_name, db_user, db_pass, db_tableprefix and conn
    Doesn't return anything
    '''
    print('==> Gathering database connection info for CubeEngine')
    print('    ==> ', end='')
    global db_hostname, db_port, db_name, db_user, db_pass, db_tableprefix
    config = yaml.load(open('./CubeEngine/database.yml').read())
    db_hostname = config['host']
    db_port = config['port']
    db_name = config['database']
    db_user = config['user']
    db_pass = config['password']
    db_tableprefix = config['table-prefix']
    print('Found connection info')
    print('    ==> ', end='')
    global conn
    conn = mysql.connect(host=config['host'], port=config['port'], user=config['user'],
                         passwd=config['password'], db=config['database'])
    cur = conn.cursor()
    cur.execute(sql_expressions['get_tables'])
    cur.close()
    print('Connected')
    print('    ==> OK')

def get_available_plugins(plugins):
    ''' Get the available plugins
    Returns a set - The available protection plugins
    '''
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
    ''' Get the database connections for the plugins
    Returns a dict - Maps from Plugin objects to Connection object
    '''
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
    ''' Get the protections from each plugin
    Returns a set - All the protections from the plugins
    '''
    print('==> Copying Protections into memory from the databases')
    protections = set()
    for plugin in connections.keys():
        print('    ==> From {}'.format(plugin.name))
        print('        ==> ', end='')
        conn = connections[plugin]
        protections.update(plugin.get_protections(conn))
        print('DONE')
    return protections
    
def insert_protections(protections):
    ''' Insert the supplied protections into Locker's database
    Doesn't return anything
    '''
    print('==> Copying protections to Locker')
    print('    ==> ', end='')
    cur = conn.cursor()
    missing = 0
    # Insert the protections
    for protection in protections:
        if "'" in protection.owner:
            continue
        try:
            sql = sql_expressions['insert_lock']\
                            .format(a=protection.owner, 
                                    b=protection.protected_type,
                                    c=protection.protection_type,
                                    d=protection.password,
                                    f="2013-01-01 00:00:00",
                                    prefix=db_tableprefix)
            cur.execute(sql)
            rowid = cur.lastrowid
            
            sql = sql_expressions['insert_locklocation']\
                            .format(a=protection.world,
                                    x=protection.x,
                                    y=protection.y,
                                    z=protection.z,
                                    cx=math.floor(protection.x/16),
                                    cz=math.floor(protection.z/16),
                                    b=rowid,
                                    prefix=db_tableprefix)
            cur.execute(sql)
            
            for user, access in protection.invited_users.items():
                if "'" in user:
                    continue
                sql = sql_expressions['insert_lockaccesslist']\
                                .format(a=user,
                                        b=rowid,
                                        c=access,
                                        prefix=db_tableprefix)
                cur.execute(sql)
        except mysql.InternalError as ex:
            if "Column \'user_id\' cannot be null" in str(ex) or\
                    "Column \'owner_id\' cannot be null" in str(ex) or\
                    "Column \'world_id\' cannot be null" in str(ex):
                missing += 1
            else:
                print('Failed to insert a home: {}'.format(repr(ex)))
                print('    ==> ', end='')
        except Exception as ex:
            if type(ex) == mysql.IntegrityError and "Duplicate entry" in str(ex):
                pass
            else:
                print('ERROR!')
                raise(ex)
    # Remove protections that doesn't have a location
    cur.execute(sql_expressions['find_without_location']\
                    .format(prefix=db_tableprefix))
    for (key,) in cur.fetchall():
        cur.execute(sql_expressions['delete_lock']\
                    .format(prefix=db_tableprefix, a=key))
        
    cur.close()
    print(("DONE - {} protections converted. {} failed because the user or"
        + " world wasn't in the database").format(str(len(protections)-missing), 
                                                 str(missing)))
    
def main():
    plugins = {'LWC': LWC()}
    available_plugins = set()
    
    print('=============== CubeEngine Locker Conversion Tool ================\n'
        + 'Welcome to CubeEngine Locker Conversion Tool, CELCT for short.\n'
        + 'This tool will autmatically detect what protect plugins you have\n'
        + 'installed and move the protections from them to Locker.');
    input()
    
    check_workspace()
    get_ce_db_info()
    available_plugins = get_available_plugins(plugins)
    database_connections = get_db_connections_plugins(available_plugins)
    protections = get_protections(database_connections)
    insert_protections(protections)
    try:
        input('Ready to commit changes to database. Press enter to continue'
            + ', or Ctrl-D to abort')
    except EOFError:
        print()
        return
    print()
    print('==> Committing changes to databases')
    print('    ==> ', end='')
    for connection in database_connections.values():
        connection.commit()
        connection.close()
    conn.commit()
    conn.close()
    print('DONE')
    print('==> DONE')
        
if __name__ == "__main__":
	main()
