import yaml
from typing import Dict, List, Tuple

class ImporterService:
    @staticmethod
    def parse_txt(filename: str, content: str) -> Dict[str, List[str]]:
        """
        Parses a wildcard .txt file (Impact Pack format).
        Returns a dictionary mapping the filename (minus extension) to a list of lines.
        """
        clean_filename = filename.replace('\\', '/')
        name = clean_filename.rsplit('.', 1)[0]
        lines = []
        for line in content.splitlines():
            line = line.strip()
            # Ignore empty lines and comments
            if line and not line.startswith('#') and not line.startswith('//'):
                lines.append(line)
        return {name: lines}

    @staticmethod
    def parse_yaml(filename: str, content: str) -> Dict[str, List[str]]:
        """
        Parses a structured .yaml file mapping wildcard keys to lists of choices.
        Flattens nested dictionaries. Supports root-level lists.
        """
        try:
            clean_filename = (filename or "wildcard.yaml").replace('\\', '/')
            base_name = clean_filename.rsplit('.', 1)[0]
            
            data = yaml.safe_load(content)
            if isinstance(data, list):
                choices = [str(item).strip() for item in data if item is not None and str(item).strip()]
                return {base_name: choices}
                
            if not isinstance(data, dict):
                return {}
                
            parsed = {}
            
            def flatten_dict(d, prefix=''):
                if not isinstance(d, dict):
                    return
                for k, v in d.items():
                    k_str = str(k).strip()
                    new_key = f"{prefix}{k_str}" if prefix else k_str
                    if isinstance(v, dict):
                        flatten_dict(v, prefix=f"{new_key}_")
                    elif isinstance(v, list):
                        parsed[new_key] = [str(item).strip() for item in v if item is not None and str(item).strip()]
                    elif v is not None:
                        parsed[new_key] = [str(v).strip()]
            
            flatten_dict(data)
            return parsed
        except Exception as e:
            print(f"Error parsing YAML ({filename}): {e}")
            return {}

    @staticmethod
    def extract_tags(lines: List[str]) -> List[str]:
        """
        Extracts individual tags from a list of strings, splitting by comma.
        Useful for building the Tag ontology database.
        """
        tags = set()
        for line in lines:
            if not line:
                continue
            line_str = str(line)
            parts = [p.strip() for p in line_str.split(',')]
            for part in parts:
                if part and len(part) < 100:  # arbitrary sane limit for a tag
                    tags.add(part)
        return list(tags)

    @staticmethod
    def export_to_txt(name: str, options: List[str]) -> str:
        """
        Exports a list of wildcard options to raw txt format.
        """
        return "\n".join(options)

    @staticmethod
    def export_to_yaml(data: Dict[str, List[str]]) -> str:
        """
        Exports a dictionary of wildcard keys and options to YAML format.
        """
        return yaml.dump(data, default_flow_style=False)

