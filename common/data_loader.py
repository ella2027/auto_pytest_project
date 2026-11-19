"""Load YAML test data from test_data/yaml/."""
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
YAML_DATA_DIR = (PROJECT_ROOT / "test_data" / "yaml").resolve()


def load_yaml(relative_path: str) -> Any:

    file_path = (YAML_DATA_DIR / relative_path).resolve()
    if YAML_DATA_DIR not in file_path.parents and file_path != YAML_DATA_DIR:
        raise ValueError("YAML path must stay inside test_data/yaml")
    if not file_path.is_file():
        raise FileNotFoundError(f"YAML test data file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)
