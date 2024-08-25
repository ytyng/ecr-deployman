from pathlib import Path

import yaml


def config_dirs():
    curdir = Path(__file__).resolve().parent.parent
    yield curdir
    yield curdir.parent


def load_config():
    """
    Read config.yaml and return it as a dict
    """
    # 親ディレクトリをいくつか確認して、config.yaml があったらパースして返す
    for d in config_dirs():
        for config_path in [
            d / 'config.yaml',
            d / 'config.yml',
        ]:
            if config_path.exists():
                with config_path.open() as f:
                    return yaml.safe_load(f)
    raise FileNotFoundError('config.yaml not found')
