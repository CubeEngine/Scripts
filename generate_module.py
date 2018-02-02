#!/usr/bin/env python

from subprocess import call
from sys import argv
from urllib import request
import re
import os


def which(program):
    for path in os.environ.get('PATH', '').split(os.pathsep):
        if os.path.exists(os.path.join(path, program)) and not os.path.isdir(os.path.join(path, program)):
            return os.path.join(path, program)
    return None


def find_latest_version_of(group_id, artifact_id, default=""):
    search_url = "http://search.maven.org/solrsearch/select?q={0}%20{1}&rows=20&wt=json".format(group_id, artifact_id)
    req = request.urlopen(search_url)
    response = req.read().decode('utf-8')
    req.close()
    match = re.search('"latestVersion":"([^"]+)"', response)
    if match is None:
        return default
    return match.group(1)


archetypeGroupId = "org.cubeengine.maven.archetypes"
archetypeArtifactId = "archetype-cubeengine-module"

if 'ARCHETYPE_VERSION' in os.environ:
    archetypeVersion = os.environ['ARCHETYPE_VERSION']
else:
    archetypeVersion = find_latest_version_of(archetypeGroupId, archetypeArtifactId, "2.0.0")


libVersion = ""
if len(argv) > 1:
    libVersion = argv[1]
else:
    libVersion = input("Enter the libcube version: ")

spongeVersion = ""
if len(argv) > 2:
    spongeVersion = argv[2]
else:
    spongeVersion = input("Enter the SpongeAPI version: ")

moduleName = ""
if len(argv) > 3:
    moduleName = argv[3]
else:
    moduleName = input("Enter the module name: ")

description = ""
if len(argv) > 4:
    description = argv[4]
else:
    description = input("Enter a short description: ")

repo = ""
if len(argv) > 5:
    repo = argv[5]
else:
    repo = input("Enter the SCM repo name (https://github.com/CubeEngine/<THIS>): ")

groupId = "org.cubeengine.module"
artifactId = re.sub(r'[^a-z]', '', moduleName.lower())

maven = "mvn"
if os.pathsep == ";":
    maven = "mvn.bat"

if 'PARENT_VERSION' in os.environ:
    parentVersion = os.environ['PARENT_VERSION']
else:
    parentVersion = find_latest_version_of("org.cubeengine", "parent", "2")

maven = which(maven)

if maven is None:
    print("I couldn't find maven in your path!")
    exit(1)

commandLine = [
    maven,
    "archetype:generate",
    "-DarchetypeGroupId=%s" % archetypeGroupId,
    "-DarchetypeArtifactId=%s" % archetypeArtifactId,
    "-DarchetypeVersion=%s" % archetypeVersion,
    "-DgroupId=%s" % groupId,
    "-DartifactId=%s" % artifactId,
    "-Dversion=%s" % "1.0.0-SNAPSHOT",
    "-Dpackage=%s.%s" % (groupId, artifactId),
    "-Ddefault-class=%s" % (artifactId[0].upper() + artifactId[1:]),
    "-DparentVersion=%s" % parentVersion,
    "-DlibVersion=%s" % libVersion,
    "-DspongeVersion=%s" % spongeVersion,
    "-Drepo=%s" % repo,
    "-Dname=%s" % moduleName,
    "-Ddescription=%s" % description,
    "-DinteractiveMode=false"
]

result = call(commandLine)

if result != 0:
    print("It seems like maven failed to generate the module...")
    print("Look at the output and press enter when you're done.")
    input()
    exit(1)
