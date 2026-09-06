from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Tuple, Set, Any
import random
import re
import os
import yaml
import bisect

@dataclass
class ASTNode:
    """Base class for AST nodes."""
    pass

@dataclass
class TextNode(ASTNode):
    text: str

@dataclass
class WildcardNode(ASTNode):
    name: str

@dataclass
class ChoiceOption:
    weight: float
    content: "RootNode"

@dataclass
class ChoiceNode(ASTNode):
    options: List[ChoiceOption]

@dataclass
class RootNode(ASTNode):
    children: List[ASTNode] = field(default_factory=list)

@dataclass
class VarAssignmentNode(ASTNode):
    var_name: str
    value_node: ASTNode

@dataclass
class VarRefNode(ASTNode):
    var_name: str

@dataclass
class MacroNode(ASTNode):
    macro_name: str
    args: List[str]

class WildcardASTEngine:
    def __init__(self, wildcards: Dict[str, List[str]] = None):
        self.wildcards = wildcards or {}
        self.variables: Dict[str, str] = {}
        self._breakdown_cache: Dict[Any, Any] = {}

    def load_from_directory(self, directory_path: str):
        self._breakdown_cache.clear()
        if not os.path.exists(directory_path):
            return

        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_dir = os.path.relpath(root, directory_path)
                
                filename_without_ext = os.path.splitext(file)[0]
                if rel_dir == ".":
                    key = filename_without_ext
                else:
                    key = f"{rel_dir}/{filename_without_ext}".replace("\\", "/")

                if file.endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                        if lines:
                            self.wildcards[key] = lines
                            if filename_without_ext not in self.wildcards:
                                self.wildcards[filename_without_ext] = lines

                elif file.endswith('.yaml') or file.endswith('.yml'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            data = yaml.safe_load(f)
                            if isinstance(data, dict):
                                for k, value in data.items():
                                    if isinstance(value, list):
                                        full_key = f"{key}/{k}" if rel_dir != "." else k
                                        val_list = [str(v) for v in value]
                                        self.wildcards[full_key] = val_list
                                        if k not in self.wildcards:
                                            self.wildcards[k] = val_list
                            elif isinstance(data, list):
                                val_list = [str(v) for v in data]
                                self.wildcards[key] = val_list
                                if filename_without_ext not in self.wildcards:
                                    self.wildcards[filename_without_ext] = val_list
                        except yaml.YAMLError:
                            pass

    def parse(self, text: str) -> RootNode:
        root, _ = self._parse_root(text, 0, stop_chars=set())
        return root

    def _parse_root(self, text: str, pos: int, stop_chars: Set[str]) -> Tuple[RootNode, int]:
        root = RootNode()
        curr_text: List[str] = []

        def flush_text():
            if curr_text:
                root.children.append(TextNode("".join(curr_text)))
                curr_text.clear()

        length = len(text)
        while pos < length:
            char = text[pos]

            if char in stop_chars:
                break

            if char == '\\' and pos + 1 < length:
                curr_text.append(text[pos + 1])
                pos += 2
                continue

            # Handle Choice Node '{'
            if char == '{':
                flush_text()
                choice_node, pos = self._parse_choice(text, pos)
                root.children.append(choice_node)
                continue

            # Handle Wildcard Node `__name__`
            if char == '_' and text[pos:pos+2] == '__':
                match = re.match(r'__([a-zA-Z0-9_/\-]+)__', text[pos:])
                if match:
                    flush_text()
                    wildcard_name = match.group(1)
                    root.children.append(WildcardNode(wildcard_name))
                    pos += len(match.group(0))
                    continue

            # Handle Variable Assignment / Ref or Macro `$name` / `$func(...)`
            if char == '$':
                # Check macro function call e.g. $range(1, 10) or $repeat(3, __wild__)
                macro_match = re.match(r'\$([a-zA-Z0-9_]+)\(([^)]*)\)', text[pos:])
                if macro_match:
                    flush_text()
                    m_name = macro_match.group(1)
                    m_args = [a.strip() for a in macro_match.group(2).split(',') if a.strip()]
                    root.children.append(MacroNode(m_name, m_args))
                    pos += len(macro_match.group(0))
                    continue

                # Check variable assignment e.g. $hero = __char__;
                var_assign_match = re.match(r'\$([a-zA-Z0-9_]+)\s*=\s*([^;]+);', text[pos:])
                if var_assign_match:
                    flush_text()
                    v_name = var_assign_match.group(1)
                    v_val_str = var_assign_match.group(2).strip()
                    val_ast = self.parse(v_val_str)
                    root.children.append(VarAssignmentNode(v_name, val_ast))
                    pos += len(var_assign_match.group(0))
                    continue

                # Check variable ref e.g. $hero
                var_ref_match = re.match(r'\$([a-zA-Z0-9_]+)', text[pos:])
                if var_ref_match:
                    flush_text()
                    v_name = var_ref_match.group(1)
                    root.children.append(VarRefNode(v_name))
                    pos += len(var_ref_match.group(0))
                    continue

            curr_text.append(char)
            pos += 1

        flush_text()
        return root, pos

    def get_wildcard_entries(self, name: str) -> Optional[List[str]]:
        """Smart resolution of wildcard names across exact match, case insensitivity, directory stripping, and fuzzy stems."""
        if not name:
            return None

        # 1. Exact match
        if name in self.wildcards:
            return self.wildcards[name]

        # 2. Case-insensitive match
        name_lower = name.lower()
        for k, v in self.wildcards.items():
            if k.lower() == name_lower:
                return v

        # 3. Strip directory / namespace prefix (e.g. mskiller/foo -> foo)
        if '/' in name or '\\' in name:
            basename = name.replace('\\', '/').split('/')[-1]
            if basename in self.wildcards:
                return self.wildcards[basename]
            basename_lower = basename.lower()
            for k, v in self.wildcards.items():
                if k.lower() == basename_lower:
                    return v
        else:
            basename_lower = name_lower

        # 4. Normalized dash / underscore match
        norm_base = basename_lower.replace('_', '-')
        for k, v in self.wildcards.items():
            norm_k = k.lower().replace('_', '-')
            if norm_k == norm_base:
                return v

        # 5. Fuzzy prefix / stem match (e.g. mklan-female-card-anima matches mklan-female-Card-anima2-full)
        for k, v in self.wildcards.items():
            norm_k = k.lower().replace('_', '-')
            if (len(norm_base) >= 5 and norm_k.startswith(norm_base)) or (len(norm_k) >= 5 and norm_base.startswith(norm_k)):
                return v

        return None

    def _parse_choice(self, text: str, pos: int) -> Tuple[ChoiceNode, int]:
        pos += 1
        options: List[ChoiceOption] = []
        length = len(text)

        while pos < length:
            weight = 1.0
            weight_match = re.match(r'^\s*(\d+(?:\.\d+)?)(?:\$\$|::)\s*', text[pos:])
            if weight_match:
                weight = float(weight_match.group(1))
                pos += len(weight_match.group(0))

            opt_root, pos = self._parse_root(text, pos, stop_chars={'|', '}'})
            options.append(ChoiceOption(weight=weight, content=opt_root))

            if pos < length and text[pos] == '|':
                pos += 1
            elif pos < length and text[pos] == '}':
                pos += 1
                break
            else:
                break

        return ChoiceNode(options=options), pos

    def evaluate(self, node: ASTNode, max_depth: int = 10, current_depth: int = 0) -> str:
        if current_depth >= max_depth:
            return self._unexpanded_str(node)

        if isinstance(node, TextNode):
            return node.text

        elif isinstance(node, RootNode):
            return "".join(self.evaluate(child, max_depth, current_depth) for child in node.children)

        elif isinstance(node, ChoiceNode):
            if not node.options:
                return ""
            weights = [opt.weight for opt in node.options]
            selected_option = random.choices(node.options, weights=weights, k=1)[0]
            return self.evaluate(selected_option.content, max_depth, current_depth)

        elif isinstance(node, WildcardNode):
            name = node.name
            entries = self.get_wildcard_entries(name)
            if entries:
                chosen_line = random.choice(entries)
                line_ast = self.parse(chosen_line)
                return self.evaluate(line_ast, max_depth, current_depth + 1)
            else:
                return f"__{name}__"

        elif isinstance(node, VarAssignmentNode):
            val_evaluated = self.evaluate(node.value_node, max_depth, current_depth)
            self.variables[node.var_name] = val_evaluated
            return ""

        elif isinstance(node, VarRefNode):
            return self.variables.get(node.var_name, f"${node.var_name}")

        elif isinstance(node, MacroNode):
            if node.macro_name == "range" and len(node.args) >= 2:
                try:
                    start = int(node.args[0])
                    stop = int(node.args[1])
                    step = int(node.args[2]) if len(node.args) >= 3 else 1
                    return str(random.choice(list(range(start, stop + 1, step))))
                except Exception:
                    pass
            elif node.macro_name == "repeat" and len(node.args) >= 2:
                try:
                    count = int(node.args[0])
                    expr = node.args[1]
                    sub_ast = self.parse(expr)
                    return ", ".join(self.evaluate(sub_ast, max_depth, current_depth) for _ in range(count))
                except Exception:
                    pass
            return f"${node.macro_name}({', '.join(node.args)})"

        return ""

    def lint_prompt(self, text: str) -> Dict[str, Any]:
        """
        Lints a prompt template and returns syntax errors, missing wildcards, and Danbooru tag category tokens.
        """
        errors = []
        warnings = []
        missing_wildcards = []
        
        # Check brace balance
        open_braces = text.count('{')
        close_braces = text.count('}')
        if open_braces != close_braces:
            errors.append(f"Mismatched braces: {open_braces} open '{{' vs {close_braces} close '}}'")

        # Parse AST and check wildcard paths
        ast = self.parse(text)
        found_wildcards = set()

        def collect_nodes(n):
            if isinstance(n, RootNode):
                for c in n.children:
                    collect_nodes(c)
            elif isinstance(n, ChoiceNode):
                for opt in n.options:
                    collect_nodes(opt.content)
            elif isinstance(n, WildcardNode):
                found_wildcards.add(n.name)
                if n.name not in self.wildcards:
                    missing_wildcards.append(n.name)
                    warnings.append(f"Wildcard file '__{n.name}__' not found in database.")

        collect_nodes(ast)

        # Categorize Danbooru tags in prompt
        tags_categorized = self.categorize_danbooru_tags(text)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "missing_wildcards": list(set(missing_wildcards)),
            "wildcards_found": list(found_wildcards),
            "extracted_wildcards": list(found_wildcards),
            "danbooru_tags": tags_categorized
        }

    def categorize_danbooru_tags(self, text: str) -> List[Dict[str, str]]:
        """
        Categorizes tags in text into Danbooru categories: artist, character, copyright, general, meta.
        """
        tags = [t.strip() for t in text.split(',') if t.strip()]
        result = []
        
        for tag in tags:
            tag_clean = tag.lower().strip()
            cat = "general"
            if tag_clean.startswith("by ") or "artist" in tag_clean:
                cat = "artist"
            elif any(c in tag_clean for c in ["girl", "boy", "hatsune miku", "character"]):
                cat = "character"
            elif any(s in tag_clean for s in ["genshin", "fate", "pokemon", "vocaloid"]):
                cat = "copyright"
            elif any(m in tag_clean for m in ["masterpiece", "highres", "absurdres", "solo"]):
                cat = "meta"

            result.append({
                "tag": tag,
                "category": cat,
                "color": {
                    "artist": "#C00000",
                    "character": "#00A000",
                    "copyright": "#A000A0",
                    "general": "#0073FF",
                    "meta": "#FF8C00"
                }[cat]
            })
        return result

    def _unexpanded_str(self, node: ASTNode) -> str:
        if isinstance(node, TextNode):
            return node.text
        elif isinstance(node, RootNode):
            return "".join(self._unexpanded_str(c) for c in node.children)
        elif isinstance(node, WildcardNode):
            return f"__{node.name}__"
        elif isinstance(node, ChoiceNode):
            opts = []
            has_explicit_weights = any(opt.weight != 1.0 for opt in node.options)
            for opt in node.options:
                content_str = self._unexpanded_str(opt.content)
                if opt.weight != 1.0 or has_explicit_weights:
                    opts.append(f"{opt.weight:g}$${content_str}")
                else:
                    opts.append(content_str)
            return f"{{{ '|'.join(opts) }}}"
        elif isinstance(node, VarAssignmentNode):
            return f"${node.var_name} = {self._unexpanded_str(node.value_node)};"
        elif isinstance(node, VarRefNode):
            return f"${node.var_name}"
        elif isinstance(node, MacroNode):
            return f"${node.macro_name}({', '.join(node.args)})"
        return ""

    def expand_prompt(self, prompt_text: str, max_depth: int = 10) -> str:
        ast = self.parse(prompt_text)
        return self.evaluate(ast, max_depth=max_depth, current_depth=0)

    def _get_wildcard_breakdown(
        self, name: str, expand_wildcards: bool = True, max_depth: int = 10, current_depth: int = 0
    ) -> Tuple[int, Optional[List[int]], Optional[List[int]], bool]:
        """
        Returns (total_count, entry_counts, cumulative_counts, is_all_plain_text).
        Memoized to ensure instant lookup even for large or repeatedly referenced wildcards.
        """
        entries = self.get_wildcard_entries(name)
        if not entries:
            return (1, None, None, True)

        cache_key = (name, id(entries), len(entries), expand_wildcards, max_depth, current_depth)
        if hasattr(self, "_breakdown_cache") and cache_key in self._breakdown_cache:
            return self._breakdown_cache[cache_key]

        if not hasattr(self, "_breakdown_cache"):
            self._breakdown_cache = {}

        # Fast path: check if all entries are plain text
        is_plain = all("{" not in e and "__" not in e and "$" not in e for e in entries)
        if is_plain:
            res = (len(entries), None, None, True)
            self._breakdown_cache[cache_key] = res
            return res

        entry_counts: List[int] = []
        cumulative_counts: List[int] = []
        cum = 0
        for e in entries:
            if "{" not in e and "__" not in e and "$" not in e:
                cnt = 1
            else:
                if current_depth >= max_depth:
                    cnt = 1
                else:
                    e_ast = self.parse(e)
                    cnt = self.count_permutations(
                        e_ast, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth + 1
                    )
            entry_counts.append(cnt)
            cum += cnt
            cumulative_counts.append(cum)

        res = (cum, entry_counts, cumulative_counts, False)
        self._breakdown_cache[cache_key] = res
        return res

    def count_permutations(
        self, node: ASTNode, expand_wildcards: bool = True, max_depth: int = 10, current_depth: int = 0
    ) -> int:
        """
        Calculates exact total number of combinatorial permutations without generating prompts in memory.
        """
        if current_depth >= max_depth:
            return 1

        if isinstance(node, TextNode):
            return 1

        elif isinstance(node, RootNode):
            if not node.children:
                return 1
            total = 1
            for child in node.children:
                cnt = self.count_permutations(
                    child, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth
                )
                if cnt == 0:
                    return 0
                total *= cnt
            return total

        elif isinstance(node, ChoiceNode):
            if not node.options:
                return 0
            return sum(
                self.count_permutations(
                    opt.content, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth
                )
                for opt in node.options
            )

        elif isinstance(node, WildcardNode):
            if not expand_wildcards:
                return 1
            total, _, _, _ = self._get_wildcard_breakdown(
                node.name, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth
            )
            return total

        elif isinstance(node, VarAssignmentNode):
            return 1

        elif isinstance(node, VarRefNode):
            return 1

        elif isinstance(node, MacroNode):
            return 1

        return 1

    def get_permutation_at_index(
        self, node: ASTNode, index: int, expand_wildcards: bool = True, max_depth: int = 10, current_depth: int = 0
    ) -> str:
        """
        Retrieves the exact permutation string at a 0-based index via mixed-radix odometer indexing in O(depth) time.
        """
        if current_depth >= max_depth:
            if index != 0:
                raise IndexError(f"Index {index} out of range for max depth reached")
            return self._unexpanded_str(node)

        if isinstance(node, TextNode):
            if index != 0:
                raise IndexError(f"Index {index} out of range for TextNode")
            return node.text

        elif isinstance(node, RootNode):
            if not node.children:
                if index != 0:
                    raise IndexError(f"Index {index} out of range for empty RootNode")
                return ""

            child_counts = [
                self.count_permutations(
                    c, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth
                )
                for c in node.children
            ]
            total_count = 1
            for c in child_counts:
                total_count *= c

            if index < 0 or index >= total_count:
                raise IndexError(f"Index {index} out of range (0..{total_count - 1})")

            m = len(node.children)
            suffix_products = [1] * m
            for k in range(m - 2, -1, -1):
                suffix_products[k] = suffix_products[k + 1] * child_counts[k + 1]

            rem = index
            parts = []
            for k in range(m):
                p = suffix_products[k]
                c_idx = rem // p
                rem = rem % p
                parts.append(
                    self.get_permutation_at_index(
                        node.children[k], c_idx, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth
                    )
                )
            return "".join(parts)

        elif isinstance(node, ChoiceNode):
            if not node.options:
                raise IndexError("Cannot index into empty ChoiceNode")
            total_count = self.count_permutations(
                node, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth
            )
            if index < 0 or index >= total_count:
                raise IndexError(f"Index {index} out of range (0..{total_count - 1})")

            curr = index
            for opt in node.options:
                cnt = self.count_permutations(
                    opt.content, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth
                )
                if curr < cnt:
                    return self.get_permutation_at_index(
                        opt.content, curr, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth
                    )
                curr -= cnt
            raise IndexError(f"Index {index} out of range")

        elif isinstance(node, WildcardNode):
            if not expand_wildcards:
                if index != 0:
                    raise IndexError(f"Index {index} out of range for unexpanded wildcard")
                return f"__{node.name}__"

            name = node.name
            entries = self.get_wildcard_entries(name)
            if not entries:
                if index != 0:
                    raise IndexError(f"Index {index} out of range for missing wildcard")
                return f"__{name}__"

            total_count, entry_counts, cumulative_counts, is_all_plain = self._get_wildcard_breakdown(
                name, expand_wildcards=expand_wildcards, max_depth=max_depth, current_depth=current_depth
            )
            if index < 0 or index >= total_count:
                raise IndexError(f"Index {index} out of range (0..{total_count - 1})")

            if is_all_plain:
                return entries[index]

            entry_idx = bisect.bisect_right(cumulative_counts, index)
            sub_idx = index if entry_idx == 0 else index - cumulative_counts[entry_idx - 1]
            raw_entry = entries[entry_idx]
            if "{" not in raw_entry and "__" not in raw_entry and "$" not in raw_entry:
                return raw_entry
            entry_ast = self.parse(raw_entry)
            return self.get_permutation_at_index(
                entry_ast, sub_idx, expand_wildcards=True, max_depth=max_depth, current_depth=current_depth + 1
            )

        elif isinstance(node, VarAssignmentNode):
            if index != 0:
                raise IndexError(f"Index {index} out of range for VarAssignmentNode")
            return ""

        elif isinstance(node, VarRefNode):
            if index != 0:
                raise IndexError(f"Index {index} out of range for VarRefNode")
            return self.variables.get(node.var_name, f"${node.var_name}")

        elif isinstance(node, MacroNode):
            if index != 0:
                raise IndexError(f"Index {index} out of range for MacroNode")
            return f"${node.macro_name}({', '.join(node.args)})"

        return ""


def serialize_ast_to_graph(node: ASTNode) -> Dict[str, Any]:
    """
    Serializes an ASTNode hierarchy into a JSON-compatible dictionary.
    """
    if isinstance(node, TextNode):
        return {"type": "TextNode", "text": node.text}
    elif isinstance(node, WildcardNode):
        return {"type": "WildcardNode", "name": node.name}
    elif isinstance(node, ChoiceNode):
        options = []
        for opt in node.options:
            options.append({
                "weight": opt.weight,
                "content": serialize_ast_to_graph(opt.content)
            })
        return {"type": "ChoiceNode", "options": options}
    elif isinstance(node, RootNode):
        return {
            "type": "RootNode",
            "children": [serialize_ast_to_graph(c) for c in node.children]
        }
    elif isinstance(node, VarAssignmentNode):
        return {
            "type": "VarAssignmentNode",
            "var_name": node.var_name,
            "value_node": serialize_ast_to_graph(node.value_node)
        }
    elif isinstance(node, VarRefNode):
        return {
            "type": "VarRefNode",
            "var_name": node.var_name
        }
    elif isinstance(node, MacroNode):
        return {
            "type": "MacroNode",
            "macro_name": node.macro_name,
            "args": list(node.args)
        }
    return {"type": "UnknownNode"}


def deserialize_graph_to_ast(graph: Dict[str, Any]) -> ASTNode:
    """
    Deserializes a JSON-compatible dictionary back into an ASTNode hierarchy.
    """
    if not isinstance(graph, dict):
        return RootNode()

    node_type = graph.get("type")
    if node_type == "TextNode":
        return TextNode(text=graph.get("text", ""))
    elif node_type == "WildcardNode":
        return WildcardNode(name=graph.get("name", ""))
    elif node_type == "ChoiceNode":
        options = []
        for opt in graph.get("options", []):
            if isinstance(opt, dict):
                content_data = opt.get("content", {})
                content_ast = deserialize_graph_to_ast(content_data)
                if not isinstance(content_ast, RootNode):
                    content_ast = RootNode(children=[content_ast])
                options.append(ChoiceOption(weight=float(opt.get("weight", 1.0)), content=content_ast))
        return ChoiceNode(options=options)
    elif node_type == "RootNode":
        children = [deserialize_graph_to_ast(c) for c in graph.get("children", []) if isinstance(c, dict)]
        return RootNode(children=children)
    elif node_type == "VarAssignmentNode":
        val_data = graph.get("value_node", {})
        val_ast = deserialize_graph_to_ast(val_data)
        return VarAssignmentNode(var_name=graph.get("var_name", ""), value_node=val_ast)
    elif node_type == "VarRefNode":
        return VarRefNode(var_name=graph.get("var_name", ""))
    elif node_type == "MacroNode":
        return MacroNode(macro_name=graph.get("macro_name", ""), args=list(graph.get("args", [])))

    return RootNode()


def sanitize_single_tag(raw: str) -> Optional[str]:
    """
    Cleans raw prompt/wildcard tokens into atomic, standardized tags:
    - Strips dynamic prompt choice syntax (e.g. {1::1::, {4::, etc.)
    - Strips SD-style weight syntax (e.g. :1.3), (tag:1.2), ((tag)) )
    - Removes punctuation and control characters
    - Discards long natural-language sentences and purely numeric tokens
    """
    if not raw:
        return None
    s = str(raw).replace('\x00', '').strip()
    if not s or s.startswith('#'):
        return None

    # Strip choice/count prefixes e.g. {1::1::, 1::, 4::, 1$$, 0.1::, etc.
    s = re.sub(r'^[\|\s]+', '', s)
    s = re.sub(r'[\|\s]+$', '', s)
    s = re.sub(r'^[\{\[\(\s]*(?:\d+(?:\.\d+)?)(?:::|\$\$|\#)', '', s)
    # Strip dangling choice syntax e.g. {4::, {1::
    s = re.sub(r'\{\d+(?:\.\d+)?::.*$', '', s)
    # Strip curly braces and pipes
    s = re.sub(r'[\{\}\|]+', '', s)

    # Strip (tag:1.2) or [tag:1.2] weight syntax
    s = re.sub(r'\(([^:)]+):\d+(?:\.\d+)?\)', r'\1', s)
    s = re.sub(r'\[([^:\]]+):\d+(?:\.\d+)?\]', r'\1', s)
    # Strip trailing weight syntax: tag:1.3) or tag:1.3
    s = re.sub(r':\d+(?:\.\d+)?\)?$', '', s)
    # Strip outer parens/brackets
    s = re.sub(r'^\(+([^\(\)]+)\)+$', r'\1', s)
    s = re.sub(r'^\[+([^\[\]]+)\]+$', r'\1', s)
    
    # Strip boundary noise
    s = s.strip('()[]{}<>"\'`;:.,~`*?!| \t\r\n')

    # Wildcard invocations (e.g. __wildcard/name__) are wildcards, not atomic prompt tags
    if re.fullmatch(r'__[^_]+__', s) or s.startswith('__') and s.endswith('__'):
        return None

    # Ignore common single English connector/stop words
    STOP_WORDS = {
        "a", "an", "the", "in", "on", "at", "by", "for", "with", "about", "against",
        "between", "into", "through", "during", "before", "after", "above", "below",
        "to", "from", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once", "and", "or"
    }
    if s.lower() in STOP_WORDS:
        return None

    # Ignore tags that are too long (>60 chars) or have too many words (>7 words)
    words = s.split()
    if not s or len(s) > 65 or len(words) > 7:
        return None


    # Ignore if no letters (e.g. pure numbers, dates, punctuation)
    if not re.search(r'[a-zA-Z\u00C0-\u024F\u3040-\u30FF\u4E00-\u9FFF]', s):
        return None

    return s.strip()


def classify_tag_category(tag: str) -> str:
    """
    Classifies a tag into a domain category:
    - Character
    - Clothing
    - Lighting
    - Style
    - Camera
    - Quality / Score
    - General
    """
    lower = tag.lower().strip()

    # Quality / Score keywords
    if any(k in lower for k in [
        'masterpiece', 'best quality', 'high quality', 'ultra-detailed', 'absurdres',
        'highres', 'photorealistic', 'hyperrealistic', '8k', '4k', 'score_', 'aesthetic',
        'trending on artstation', 'award winning'
    ]):
        return 'Quality / Score'

    # Camera / Angle / Shot
    if any(k in lower for k in [
        'view', 'angle', 'shot', 'focus', 'depth of field', 'dof', 'bokeh',
        'close-up', 'close up', 'wide shot', 'cowboy shot', 'portrait', 'full body',
        'upper body', 'macro', 'fisheye', 'telephoto', 'isometric', 'lens', 'shutter'
    ]):
        return 'Camera'

    # Lighting keywords
    if any(k in lower for k in [
        'light', 'glow', 'shadow', 'illumination', 'sunlight', 'moonlight',
        'neon', 'backlight', 'rim light', 'cinematic lighting', 'volumetric',
        'soft lighting', 'golden hour', 'ray tracing', 'radiance', 'bloom'
    ]):
        return 'Lighting'

    # Style / Medium / Artist keywords
    if any(k in lower for k in [
        'cyberpunk', 'steampunk', 'synthwave', 'anime', 'manga', 'comic', 'oil painting',
        'watercolor', 'digital illustration', 'concept art', 'minimalist', 'retro',
        'surrealism', 'line art', 'vintage', 'dark fantasy', 'render', 'unreal engine',
        'octane render', 'by ', 'art by'
    ]):
        return 'Style'

    # Clothing / Fashion keywords
    if any(k in lower for k in [
        'dress', 'shirt', 'jacket', 'coat', 'pants', 'jeans', 'skirt', 'boots',
        'shoes', 'hat', 'hoodie', 'suit', 'armor', 'uniform', 'robe', 'gloves',
        'collar', 'necklace', 'kimono', 'sweater', 'bikini', 'socks', 'stockings'
    ]):
        return 'Clothing'

    # Character / Subject keywords
    if any(k in lower for k in [
        'girl', 'boy', 'woman', 'man', 'solo', 'female', 'male', 'hair', 'eyes',
        'skin', 'smile', 'face', 'gaze', 'pose', 'standing', 'sitting', 'looking at viewer',
        'expression', 'breasts', 'muscular', 'wings', 'horns', 'tail', 'ears'
    ]):
        return 'Character'

    return 'General'


def extract_atomic_tags_from_text(text: str) -> List[Tuple[str, str]]:
    """
    Parses prompt/wildcard text through the AST engine, collects text leaves
    and choice option contents, splits by comma or pipe, sanitizes each tag,
    classifies its category, and returns deduplicated (tag_name, category) pairs.
    """
    if not text:
        return []

    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith('#')]
    if not lines:
        return []

    engine = WildcardASTEngine()
    collected_strings: List[str] = []

    def collect_from_ast(node: ASTNode):
        if isinstance(node, TextNode):
            collected_strings.append(node.text)
        elif isinstance(node, RootNode):
            for child in node.children:
                collect_from_ast(child)
        elif isinstance(node, ChoiceNode):
            for opt in node.options:
                collect_from_ast(opt.content)
        elif isinstance(node, VarAssignmentNode):
            collect_from_ast(node.value_node)

    for line in lines:
        try:
            root = engine.parse(line)
            collect_from_ast(root)
        except Exception:
            collected_strings.append(line)

    seen_lower = set()
    result: List[Tuple[str, str]] = []

    for chunk in collected_strings:
        # Split chunk on comma or pipe
        parts = re.split(r'[,\|]', chunk)
        for p in parts:
            clean = sanitize_single_tag(p)
            if clean and clean.lower() not in seen_lower:
                seen_lower.add(clean.lower())
                cat = classify_tag_category(clean)
                result.append((clean, cat))

    return result

