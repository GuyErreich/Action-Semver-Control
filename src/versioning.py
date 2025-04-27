class VersionManager:
    def __init__(self, current_version: str) -> None:
        self.major, self.minor, self.patch = map(int, current_version.split('.')[:3])

    def bump(self, bump_type: str, suffix: str | None) -> str:
        if bump_type == 'major':
            self.major += 1
            self.minor = 0
            self.patch = 0
        elif bump_type == 'minor':
            self.minor += 1
            self.patch = 0
        elif bump_type == 'patch':
            self.patch += 1
        else:
            raise ValueError(f"Unknown bump type: {bump_type}")

        version = f"{self.major}.{self.minor}.{self.patch}"
        if suffix:
            version += suffix
        return version

    @staticmethod
    def detect_bump_type(branch_name: str) -> str:
        if branch_name.startswith(('breaking/', 'major/')):
            return 'major'
        if branch_name.startswith(('feature/',)):
            return 'minor'
        if branch_name.startswith(('fix/', 'bug/', 'hotfix/', 'chore/', 'devops/')):
            return 'patch'
        return 'patch'