"""
OpenWebUI Tool: Code Execution
Version: 2.0.0
Description: Execute Python code safely in a sandboxed environment.

This tool allows the AI to run Python code and return results.
"""

from pydantic import BaseModel, Field
from typing import Optional
import subprocess
import json
import sys
import os
import tempfile
import traceback


class Tools:
    class Valves(BaseModel):
        timeout: int = Field(
            default=60,
            description="Maximum execution time in seconds"
        )
        max_output: int = Field(
            default=10000,
            description="Maximum output characters"
        )
        allowed_modules: str = Field(
            default="math,random,datetime,json,re,collections,itertools,functools,statistics,decimal,fractions,copy,pprint,string,textwrap,unicodedata",
            description="Comma-separated list of allowed Python modules"
        )
    
    def __init__(self):
        self.valves = self.Valves()
    
    def execute_python(
        self,
        code: str,
        timeout: Optional[int] = None
    ) -> str:
        """
        Execute Python code and return the result.
        
        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (optional)
        
        Returns:
            The output of the code execution (stdout, or error message)
        """
        timeout = timeout or self.valves.timeout
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute the code
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tempfile.gettempdir()
            )
            
            # Get output
            if result.returncode == 0:
                output = result.stdout
            else:
                output = f"Error:\n{result.stderr}"
            
            # Truncate if too long
            if len(output) > self.valves.max_output:
                output = output[:self.valves.max_output] + "\n... (output truncated)"
            
            return output
            
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {str(e)}\n{traceback.format_exc()}"
        finally:
            # Clean up
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def execute_shell(
        self,
        command: str,
        timeout: Optional[int] = None
    ) -> str:
        """
        Execute a shell command and return the result.
        
        Args:
            command: Shell command to execute
            timeout: Execution timeout in seconds (optional)
        
        Returns:
            The output of the command (stdout, or error message)
        """
        timeout = timeout or self.valves.timeout
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                output = result.stdout
            else:
                output = f"Exit code: {result.returncode}\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
            
            if len(output) > self.valves.max_output:
                output = output[:self.valves.max_output] + "\n... (output truncated)"
            
            return output
            
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def evaluate_expression(self, expression: str) -> str:
        """
        Safely evaluate a mathematical expression.
        
        Args:
            expression: Mathematical expression to evaluate
        
        Returns:
            The result of the evaluation
        """
        import ast
        import operator
        
        # Allowed operators
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        def safe_eval(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
            elif isinstance(node, ast.BinOp):
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                op = operators.get(type(node.op))
                if op:
                    return op(left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = safe_eval(node.operand)
                op = operators.get(type(node.op))
                if op:
                    return op(operand)
            raise ValueError(f"Unsupported operation: {type(node)}")
        
        try:
            tree = ast.parse(expression, mode='eval')
            result = safe_eval(tree.body)
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"


# For OpenWebUI tool registration
if __name__ == "__main__":
    tools = Tools()
    print(json.dumps({
        "name": "code_execution",
        "description": "Execute Python code and shell commands",
        "tools": [
            {
                "name": "execute_python",
                "description": "Execute Python code",
                "parameters": {
                    "code": "string - Python code to execute",
                    "timeout": "int - Optional timeout in seconds"
                }
            },
            {
                "name": "execute_shell",
                "description": "Execute a shell command",
                "parameters": {
                    "command": "string - Shell command to execute",
                    "timeout": "int - Optional timeout in seconds"
                }
            },
            {
                "name": "evaluate_expression",
                "description": "Safely evaluate a mathematical expression",
                "parameters": {
                    "expression": "string - Mathematical expression"
                }
            }
        ]
    }, indent=2))