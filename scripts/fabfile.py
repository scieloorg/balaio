# coding: utf-8
from fabric.api import (
    task,
    run,
    cd,
    prefix,
    sudo,
)
from fabric.context_managers import settings

from fabfile_settings import deploy_envs as app_settings


@task
def reload(env):
    with cd(app_settings[env]['installation_path']):
        run('make reload')


@task
def update(env):
    """
    Update an instance running on a remote server.
    """
    if env not in app_settings:
        exit('unknown deploy environment. is it configured in fabfile_settings.py?')

    with cd(app_settings[env]['installation_path']):
        with prefix('source %s/bin/activate' % app_settings[env]['venv_path']):
            # stash modifications to apply them later
            run('git stash')
            run('git pull origin master')
            run('git stash pop')

    reload(env)

