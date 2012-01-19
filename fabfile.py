from __future__ import with_statement
from fabric.api import *
from fabric.colors import green

# Local testing


def test():
    """
    Run tests for django_webid.auth
    """
    local("python ./run_tests.py")
    print("")
    print(green("[OK] Tests were passed ok!"))


def init():
    """
    Initialize a virtualenv in which to run tests against this
    """
    local("virtualenv .")
    local("pip install -E . -r ./requirements.pip")
    local("python setup.py sdist")
    local("pip install -E . dist/python-webid-0.1.tar.gz")
    print(green("[OK] env has been initializated"))


def rebuild():
    """
    re-builds the package
    """
    local("rm -rf dist/")
    local("python setup.py sdist")
    local("pip install -E . -I -U dist/python-webid-0.1.tar.gz")
    print(green("[OK] env has been rebuilt"))


def clean():
    """
    Remove the cruft created by virtualenv and pip
    """
    local("rm -rf bin/ include/ lib/ dist/")
    print(green("[OK] env has been cleaned"))



##############################################
# Deployment
##############################################

#execfile('.PROD')


def deploy():
    code_dir = env.code_dir
    repo = env.repo
    with settings(warn_only=True):
        if run("test -d %s" % code_dir).failed:
            run("git clone %s %s" % (repo, code_dir))
    with cd(code_dir):
        run("git pull origin master")
        run("~/webid_scripts/python-webid_build.sh")
    print("")
    print(green("[OK] Code has been deployed"))


def init_and_deploy():
    code_dir = env.code_dir
    repo = env.repo
    with settings(warn_only=True):
        if run("test -d %s" % code_dir).failed:
            run("git clone %s %s" % (repo, code_dir))
    with cd(code_dir):
        run("git pull origin master")
        run("~/webid_scripts/python-webid_init_and_build.sh")
    print("")
    print(green("[OK] Code has been deployed"))
