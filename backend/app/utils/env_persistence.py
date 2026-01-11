from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_env_file_path() -> Path:
    backend_dir = Path(__file__).parent.parent.parent
    return backend_dir / ".env"


def read_env_file(env_file: Path) -> Dict[str, str]:
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def write_env_file(env_file: Path, env_vars: Dict[str, str]) -> None:
    with open(env_file, 'w') as f:
        f.write("# Lens Configuration\n")
        f.write("# Auto-generated from settings panel\n\n")
        
        ai_keys = ["AI_ENABLED", "OPENAI_BASE_URL", "OPENAI_API_KEY", 
                   "OPENAI_MODEL", "OPENAI_MAX_TOKENS", "OPENAI_TEMPERATURE", 
                   "OPENAI_TIMEOUT"]
        has_ai_settings = any(key in env_vars for key in ai_keys)
        
        if has_ai_settings:
            f.write("# AI Configuration\n")
            for key in ai_keys:
                if key in env_vars:
                    f.write(f"{key}={env_vars[key]}\n")
            f.write("\n")
        
        if "LOG_LEVEL" in env_vars:
            f.write("# Logging Configuration\n")
            f.write(f"LOG_LEVEL={env_vars['LOG_LEVEL']}\n")
            f.write("\n")
        
        other_keys = [k for k in env_vars.keys() if k not in ai_keys and k != "LOG_LEVEL"]
        if other_keys:
            f.write("# Other Settings\n")
            for key in other_keys:
                f.write(f"{key}={env_vars[key]}\n")


def update_env_file(updates: Dict[str, Any], key_mapping: Dict[str, str]) -> None:
    env_file = get_env_file_path()
    env_vars = read_env_file(env_file)
    
    for config_key, value in updates.items():
        if config_key in key_mapping:
            env_key = key_mapping[config_key]
            if isinstance(value, bool):
                env_vars[env_key] = "true" if value else "false"
            else:
                env_vars[env_key] = str(value)
    
    write_env_file(env_file, env_vars)
    logger.info(f"Updated .env file with keys: {', '.join(key_mapping.get(k, k) for k in updates.keys() if k in key_mapping)}")
