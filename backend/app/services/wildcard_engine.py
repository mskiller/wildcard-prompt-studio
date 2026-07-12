import random
import re
from typing import Dict, List

class WildcardEngine:
    def __init__(self, wildcards: Dict[str, List[str]] = None):
        """
        Initialize the WildcardEngine with a dictionary of wildcards.
        For example: {"character": ["elf", "knight"], "color": ["red", "blue"]}
        """
        self.wildcards = wildcards or {}

    def expand_prompt(self, prompt_text: str, max_depth: int = 10) -> str:
        """
        Expand wildcards and inline choices in a prompt string.
        """
        return self._expand(prompt_text, max_depth, 0)

    def _expand(self, text: str, max_depth: int, current_depth: int) -> str:
        if current_depth >= max_depth:
            return text
            
        changed = False
        result = text
        
        # 1. Expand __wildcard_name__
        def repl_wildcard(match):
            nonlocal changed
            name = match.group(1)
            if name in self.wildcards and self.wildcards[name]:
                changed = True
                return str(random.choice(self.wildcards[name]))
            return match.group(0)
            
        result = re.sub(r'__([a-zA-Z0-9_/\-]+)__', repl_wildcard, result)
        
        # 2. Expand {a|b|c} inline choices
        # Using [^{}]* allows processing innermost choices first.
        def repl_inline(match):
            nonlocal changed
            options = match.group(1).split('|')
            changed = True
            return str(random.choice(options))
            
        result = re.sub(r'\{([^{}]*)\}', repl_inline, result)
        
        # If any substitution was made, continue expanding recursively
        if changed and current_depth + 1 < max_depth:
            return self._expand(result, max_depth, current_depth + 1)
            
        return result
