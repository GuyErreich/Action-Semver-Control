import git

def ensure_git_safe_directory(path: str) -> None:
    repo = git.Repo(path)
    git_config = repo.config_writer(config_level='global')

    try:
        safe_dirs = git_config.get_value('safe', 'directory')
        if isinstance(safe_dirs, str):
            safe_dirs = [safe_dirs]
    except Exception:
        safe_dirs = []

    if path not in safe_dirs:
        git_config.set_value('safe', 'directory', path)
        git_config.release()