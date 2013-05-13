import _mysql
from sys import argv
import sys
import string
import random

def name_generator(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

USERS = 1000
TELEPORTPOINTS = 10000
INVITES = 5000

conn = None

try:

    conn = _mysql.connect(str(argv[1]), str(argv[2]), str(argv[3]), str(argv[4])) #Host, user, password, database
    print "Creating 1000 users, 10 000 teleportpoints and 3000 invites"
    print "Creating Users"    
    for x in range(USERS):
        conn.query("INSERT  INTO cube_user (player, nogc, lastseen, passwd, firstseen, language) VALUES ('%s', 0, '2013-04-01 00:00:01', '', '2013-01-01 00:00:01', 'NULL')" % name_generator())
        message = "%i of %i" % (x, USERS)
        sys.stdout.write(message)
        sys.stdout.write("\b" * len(message))
        sys.stdout.flush()
    print "Done creating users"
    print "Creating Homes and Warps"
    for x in range(TELEPORTPOINTS):
        conn.query("INSERT IGNORE INTO cube_teleportpoints (owner, type, visibility, world, x, y, z, yaw, pitch, name, permission) VALUES (%i, %i, %i, 1, %i, %i, %i, 0, 45, '%s', %i)" %
            (random.randint(1,USERS), random.randint(0,1), random.randint(0,1), random.randint(-10000,10000), random.randint(-10000,10000), random.randint(-10000,10000), name_generator(), random.randint(0,1)))
        message = "%i of %i" % (x, TELEPORTPOINTS)
        sys.stdout.write(message)
        sys.stdout.write("\b" * len(message))
        sys.stdout.flush()
    print "Done creating Homes and Warps"
    print "Creating invites"
    for x in range(INVITES):
        conn.query("INSERT IGNORE INTO cube_teleportinvites (teleportpoint, userkey) VALUES (%i, %i)" % (random.randint(1,TELEPORTPOINTS), random.randint(1,USERS)))
        message = "%i of %i" % (x, INVITES)
        sys.stdout.write(message)
        sys.stdout.write("\b" * len(message))
        sys.stdout.flush()
    print "Done creating invites"
    print "DONE!"
except _mysql.Error as e:
  
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit(1)

finally:
    if conn:
        conn.close()
