from typing import Any, Dict, Optional, Union

import click

from valohai_cli.exceptions import NoProject
from valohai_cli.messages import success
from valohai_cli.models.project import Project
from valohai_cli.models.remote_project import RemoteProject
from valohai_cli.settings import settings
from valohai_cli.utils import get_project_directory


def get_project(
    dir: Optional[str] = None, require: bool = False
) -> Optional[Union[Project, RemoteProject]]:
    """
    Get the Valohai project object for a directory context.

    The directory tree is walked upwards to find an actual linked directory.

    :param dir: Directory (defaults to cwd)
    :param require: Raise an exception if no project is found
    :return: Project object, or None.
    :rtype: valohai_cli.models.project.Project|None
    """
    dir = dir or get_project_directory()
    project = settings.get_project(dir)
    if not project and require:
        raise NoProject('No project is linked to %s' % dir)
    return project


def set_project_link(
    dir: str,
    project: Dict[str, Any],
    inform: bool = False,
) -> None:
    settings.set_project_link(dir, project)
    if inform:
        success(
            'Linked {dir} to {name}.'.format(
                dir=click.style(dir, bold=True),
                name=click.style(project['name'], bold=True),
            )
        )
