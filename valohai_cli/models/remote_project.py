from valohai_cli.models.project import Project
from typing import Optional
from valohai_yaml.objs.config import Config


class RemoteProject(Project):
    is_remote = True

    def get_config(self, commit_identifier: Optional[str]=None) -> Config:
        if not commit_identifier:
            raise ValueError('RemoteProjects require an explicit commit identifier')
        commit = self.load_full_commit(commit_identifier)
        if not commit:
            raise ValueError(f'No configuration found for commit {commit_identifier}')
        return self._parse_config(commit['config'], filename='<remote config>')

    def get_config_filename(self) -> str:  # pragma: no cover  # typing: ignore[override]
        raise NotImplementedError('RemoteProject.get_config_filename() should never get called')
