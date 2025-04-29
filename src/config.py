import yaml

CONFIG_FILE = "auto_semver_config.yml"

class Config:
    def __init__(self, path: str = CONFIG_FILE) -> None:
        with open(path, 'r') as f:
            self.data: dict = yaml.safe_load(f)

    def get_start_version(self) -> str:
        return self.data.get('start_version', '0.1.0')

    def get_suffix(self, target_branch: str) -> str:
        return self.data.get('suffixes', {}).get(target_branch, '')

    def get_branch_strategy(self) -> str:
        return self.data.get('branch_strategy', 'single')

    def get_files_to_update(self) -> list[str]:
        files_to_update = self.data.get('files_to_update', [])
        
        if CONFIG_FILE in files_to_update:
            raise ValueError(f"Do not list the config file '{CONFIG_FILE}' in files_to_update.")

        return files_to_update