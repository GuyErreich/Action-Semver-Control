class VersionManager:
    def __init__(self, current_version: str) -> None:
        self.major, self.minor, self.patch = map(int, current_version.split('.')[:3])


    @staticmethod
    def detect_bump_type(branch_name: str) -> str:
        if branch_name.startswith(('breaking/', 'major/')):
            return 'major'
        if branch_name.startswith(('feature/',)):
            return 'minor'
        if branch_name.startswith(('fix/', 'bug/', 'hotfix/', 'chore/', 'devops/')):
            return 'patch'
        return 'patch'