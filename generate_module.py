from subprocess import call
from time import sleep
from sys import argv
import re
import os

def which(program):
    for path in os.environ.get('PATH', '').split(os.pathsep):
        if os.path.exists(os.path.join(path, program)) and \
           not os.path.isdir(os.path.join(path, program)):
            return os.path.join(path, program)
    return None

archetypeGroupId = "de.cubeisland.maven"
archetypeArtifactId = "cubeengine-module"
archetypeVersion = "1.0.0-SNAPSHOT"

defaultCoreVersion = "1.0.0-SNAPSHOT"

moduleName = ""
if len(argv) > 1:
    moduleName = argv[1]
else:
    moduleName = input("Enter the module name: ")

description = "";
if len(argv) > 2:
    description = argv[2]
else:
    description = input("Enter a short description: ")

coreVersion = defaultCoreVersion
if len(argv) > 3:
    coreVersion = argv[3]
else:
    coreVersion = input("Enter the core version [%s]: " % defaultCoreVersion).strip()
    if not len(coreVersion):
        coreVersion = defaultCoreVersion

groupId = "de.cubeisland.cubeengine"
artifactId = re.sub(r'[^a-z]', '', moduleName.lower());

maven = "mvn";
if os.pathsep == ";":
    maven = "mvn.bat"

maven = which(maven)

commandLine = [
    maven,
    "archetype:generate",
    "-DarchetypeGroupId=%s" % archetypeGroupId,
    "-DarchetypeArtifactId=%s" % archetypeArtifactId,
    "-DarchetypeVersion=%s" % archetypeVersion,
    "-DgroupId=%s" % groupId,
    "-DartifactId=%s" % artifactId,
    "-Dversion=%s" % coreVersion,
    "-Dpackage=%s.%s" % (groupId, artifactId),
    "-Ddefault-class=%s" % (artifactId[0].upper() + artifactId[1:]),
    "-Dname=%s" % moduleName,
    "-Ddescription=%s" % description
]

#print(commandLine)
#sleep(5)

call(commandLine)
