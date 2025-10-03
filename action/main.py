#!/usr/bin/env python3
import os
import re
import json
import yaml
from pathlib import Path

def load_file(path: Path):
    if not path.exists():
        print(f"::warning:: File {path} not found, skip.")
        return {}
    if path.suffix.lower() in [".yaml", ".yml"]:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data else {}
    elif path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    elif path.suffix.lower() == ".env":
        result = {}
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    result[k.strip()] = v.strip()
        return result
    else:
        print(f"::warning:: Unsupported file type {path.suffix}, skip.")
        return {}

def flatten_dict(d, parent_key="", sep="__"):
    """Flatten nested dictionaries into a single level with KEY__SUBKEY format."""
    items = []
    for k, v in (d or {}).items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def replace_refs(mapping):
    """Resolve $(Var) style references recursively."""
    pattern = re.compile(r"\$\(([^)]+)\)")
    resolved = dict(mapping)
    # Iterate up to 10 times to avoid infinite loops
    for _ in range(10):
        changed = False
        for k, v in list(resolved.items()):
            if isinstance(v, str):
                def _sub(match):
                    varname = match.group(1)
                    return str(resolved.get(varname, f"$({varname})"))
                new_v = pattern.sub(_sub, v)
                if new_v != v:
                    resolved[k] = new_v
                    changed = True
        if not changed:
            break
    return resolved

def extract_ado_variables(data):
    """Extract the 'variables:' node if present in an ADO YAML file."""
    if not isinstance(data, dict):
        return {}
    if "variables" in data and isinstance(data["variables"], dict):
        return data["variables"]
    # Also support the list format: variables: [ {name: "x", value: "y"} ]
    if "variables" in data and isinstance(data["variables"], list):
        result = {}
        for item in data["variables"]:
            if isinstance(item, dict) and "name" in item and "value" in item:
                result[item["name"]] = item["value"]
        return result
    return data

def safe_write_env_line(f, key: str, value: str):
    """
    Write environment variables to GITHUB_ENV safely.
    If the value contains special characters (backslashes, %, :, =, newlines, etc.)
    use the multi-line <<EOF format as recommended by GitHub.
    """
    if any(c in value for c in ['\n', '\r', '\\', '%', '=', ':']):
        f.write(f"{key}<<EOF\n{value}\nEOF\n")
    else:
        f.write(f"{key}={value}\n")

def main():
    files_input = os.environ.get("INPUT_FILES", "")
    prefix = os.environ.get("INPUT_PREFIX", "")
    all_vars = {}
    for f in [s.strip() for s in files_input.split(",") if s.strip()]:
        path = Path(f)
        raw = load_file(path)
        raw = extract_ado_variables(raw)
        flat = flatten_dict(raw)
        all_vars.update(flat)
    # Resolve variable references like $(Var)
    all_vars = replace_refs(all_vars)
    # Write to GITHUB_ENV safely
    env_file = os.getenv("GITHUB_ENV")
    with open(env_file, "a", encoding="utf-8") as f:
        for k, v in all_vars.items():
            key = f"{prefix}{k}" if prefix else k
            safe_write_env_line(f, key, str(v))
            print(f"Exported: {key}={v}")

if __name__ == "__main__":
    main()
