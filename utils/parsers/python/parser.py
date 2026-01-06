# remove blank lines before splitting
# blank line is breaking the code
import re
import ast

def has_unclosed_multiline_comment(code: str) -> bool:
    triple_quote_pattern = re.compile(r"('''|\"\"\")")

    # Remove escaped triple quotes and comments
    code = re.sub(r'\\("""|\'\'\')', '', code)
    code = re.sub(r'#.*', '', code)  # Remove inline comments

    # Find all triple quote occurrences
    quotes = triple_quote_pattern.findall(code)
    # print(len(quotes))

    # Count of triple quotes must be even for all to be closed
    return len(quotes) % 2 != 0

class PythonBlockParser:
    def seperateImport(self,code):
        import_lines = []
        tree = ast.parse(code)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_lines.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    import_lines.append(f"from {module} import {alias.name}")

        return import_lines
    
    def chunkHasMultiLineComment(self,chunk):
        if '"""' in chunk or "'''" in chunk:
            return True
        return False
    
    def mergeMultiLineComment(self, chunks):
        add_to_previous = False
        memory = []
        sorted_chunks = []

        for chunk in chunks:
            memory.append(chunk)

            if self.chunkHasMultiLineComment(chunk):
                if has_unclosed_multiline_comment(chunk):
                    add_to_previous = not add_to_previous

            if not add_to_previous:
                # Only append when multiline comment block is fully closed
                sorted_chunks.append("\n".join(memory))
                memory = []  # Clear for next block

        # If memory still has content at the end (e.g. unclosed comment at end of file)
        if memory:
            sorted_chunks.append("\n".join(memory))

        return sorted_chunks
    
    def clean_parsed_code(self,chunks):
        chunks = self.mergeMultiLineComment(chunks)
        """
        Process and clean parsed code chunks by handling import statements and combining related code segments.

        This method processes a list of code chunks by:
        1. Separating multiple imports into individual import statements
        2. Combining consecutive chunks that belong together (except for decorator lines)
        3. Managing a temporary memory buffer for related code segments

        Args:
            chunks (list): A list of string chunks containing Python code segments

        Returns:
            list: A processed list of code chunks where:
                - Multiple imports are split into separate chunks
                - Related code segments are combined
                - Decorators are handled separately

        Example:
            For input chunks:
            ['import os, sys', '@decorator\n', 'def func():\n    pass']
            
            Returns:
            ['import os', 'import sys', '@decorator\ndef func():\n    pass']
        """
        processed_chunks = []
        memory = []
        add_to_previous = False

        for chunk in chunks:
            if chunk.startswith("import ") or chunk.startswith("from "):
                if chunk.count("import ") > 1:
                    for i in self.seperateImport(chunk):
                        if i.startswith("import "):
                            processed_chunks.extend(self.split_packed_imports(i))
                        else:
                            processed_chunks.append(i)
                else:
                    if chunk.startswith("import "):
                        processed_chunks.extend(self.split_packed_imports(chunk))
                    else:
                        processed_chunks.append(chunk)
                continue #start over

            memory.append(chunk)

            if not chunk.startswith("@"):
                processed_chunks.append("\n".join(memory))
                memory = [] #clear memory

        return processed_chunks
    
    def split_packed_imports(self,chunk):
        """
        Splits packed import statements into individual import statements.
        This method processes a chunk of Python code containing multiple imports 
        separated by commas and converts them into separate import statements.
        Args:
            chunk (str): A string containing one or more import statements potentially
                         separated by commas.
        Returns:
            Union[str, List[str]]: If the chunk starts with '#', returns the original chunk.
                                  Otherwise, returns a list of individual import statements.
        Examples:
            >>> split_packed_imports("import os, sys")
            ['import os', 'import sys']
            >>> split_packed_imports("# import comment")
            '# import comment'
        """
        if chunk.startswith("#"):
            return chunk
        
        imports = ["import "+pack.strip() for pack in chunk.replace("import ","").split(",")]
        return imports
    
    def parse_code(self, code_string):
        """Parse Python code into top-level blocks."""
        lines = code_string.split('\n')
        
        blocks = []
        current_block = []
        stack = []  # For tracking delimiters (), [], {}
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Skip empty lines between blocks
            if not line.strip():
                if current_block:
                    blocks.append('\n'.join(current_block))

                    current_block = []
                i += 1
                continue
            
            # Calculate indentation
            indent = len(line) - len(line.lstrip())
            
            # Start of a new block
            if not current_block:
                current_block = [line]
                stack = self._update_delimiter_stack(line, [])
                i += 1
                continue
            
            # If we're at the top level (no indent) and there's no open delimiters
            if indent == 0 and not stack and not self._is_incomplete_line(current_block[-1]):
                stripped = line.lstrip()
                # If this is a new top-level construct, start a new block
                if not (stripped.startswith(('elif', 'else', 'except', 'finally'))):
                    blocks.append('\n'.join(current_block))
                    current_block = [line]
                    stack = self._update_delimiter_stack(line, [])
                else:
                    # Continue the current block for elif/else/except/finally
                    current_block.append(line)
            else:
                # Add to current block
                current_block.append(line)
                stack = self._update_delimiter_stack(line, stack)
            
            i += 1
        
        # Add the last block if exists
        if current_block:
            blocks.append('\n'.join(current_block))
        
        if len(blocks) == 0:
            return []
        
        new_blocks = [blocks[0]]

        for i in range(1,len(blocks)):
            chunk = blocks[i]
            # print(f"line {chunk}\n\n")
            stack = []
            lines = chunk.split("\n")
            # print(type(chunk)," ",chunk)

            for line in lines:
                stack,has_close_but_no_opening = self._has_close_but_no_opening(line.strip(),stack)


            if chunk.startswith("    ") or has_close_but_no_opening:
                new_blocks[-1] += f"\n\n{chunk}"
            else:
                new_blocks.append(chunk)

        return self.clean_parsed_code(new_blocks)
    
    def _update_delimiter_stack(self, line, stack):
        """Update the stack of delimiters for the line."""
        delimiters = {'(': ')', '[': ']', '{': '}'}
        
        for char in line:
            if char in delimiters:
                stack.append(char)
            elif char in delimiters.values():
                if stack and delimiters[stack[-1]] == char:
                    # print("popping ",line)
                    stack.pop()
        
        return stack
    
    def _has_close_but_no_opening(self, line, stack):
        """Update the stack of delimiters for the line."""
        delimiters = {'(': ')', '[': ']', '{': '}'}
        has_close_but_no_opening = False

        for char in line:
            if char in delimiters:
                stack.append(char)
            elif char in delimiters.values():
                if stack and delimiters[stack[-1]] == char:
                    # print("popping ",line)
                    has_close_but_no_opening = False
                    stack.pop()
                else:
                    has_close_but_no_opening = True
        
        return [stack,has_close_but_no_opening]
    
    def _is_incomplete_line(self, line):
        """Check if the line appears incomplete (e.g., ends with operator)."""
        operators = ['=', '+', '-', '*', '/', '%', '&', '|', '^', ',0', '\\']
        stripped = line.rstrip()
        return any(stripped.endswith(op) for op in operators)



# def unindentCode(code):
#     block = []
#     lines = code.split("\n")
#     start = lines[0]
#     indent = 0

#     for char in start:
#         if char == " ":
#             indent += 1

#     for line in lines:
#         while len(line[:indent].strip()) > 0:
#             indent -= 1

#         block.append(line[indent:].strip())
    
#     return "\n".join(block)

def unindentCode(code):
    block = []
    lines = code.split("\n")

    for line in lines:
        if len(line.strip()) > 0:
            _,code = line.split("    ",1)  
            # print("code is",code)          
            block.append(code)
    
    return "\n".join(block)

def indentCode(code, indent=4):
    block = []
    lines = code.split("\n")
    # start = lines[0]

    for line in lines:
        block.append(f"{" "*indent}{line}")
    
    return "\n".join(block) 
    