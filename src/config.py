import yaml

class Config:
    def __init__(self, path: str = "auto_semver_config.yml") -> None:
        with open(path, 'r') as f:
            self.data: dict = yaml.safe_load(f)

    def get_start_version(self) -> str:
        return self.data.get('start_version', '0.1.0')

    def get_suffix(self, target_branch: str) -> str:
        return self.data.get('suffixes', {}).get(target_branch, '')

    def get_branch_strategy(self) -> str:
        return self.data.get('branch_strategy', 'single')

    def get_files_to_update(self) -> list[str]:
        return self.data.get('files_to_update', [])