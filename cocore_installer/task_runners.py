import os
import subprocess
import tempfile
import json
import time
import traceback
import requests
from task_installers import TaskInstallers
from task_extensions import DEMARCATION
class TaskRunners:
    
    @classmethod
    def run_node_task(cls, task_requirements, task_code, args, task_extension):
        return cls.run_language_task(
            language="node",
            task_requirements=task_requirements,
            task_code=task_code,
            args=args,
            task_extension=task_extension,
            installer=TaskInstallers.install_node_packages,
            interpreter_command="node",
            file_extension=".js"
        )

    @classmethod
    def run_ruby_task(cls, task_requirements, task_code, args, task_extension):
        return cls.run_language_task(
            language="ruby",
            task_requirements=task_requirements,
            task_code=task_code,
            args=args,
            task_extension=task_extension,
            installer=TaskInstallers.install_ruby_gems,
            interpreter_command="ruby",
            file_extension=".rb"
        )

    @classmethod
    def run_python_task(cls, task_requirements, task_code, args, task_extension):
        return cls.run_language_task(
            language="python",
            task_requirements=task_requirements,
            task_code=task_code,
            args=args,
            task_extension=task_extension,
            installer=TaskInstallers.install_python_packages,
            interpreter_command="python",
            file_extension=".py"
        )

    @classmethod
    def run_go_task(cls, task_requirements, task_code, args, task_extension):
        package_declaration, go_imports, go_non_import_code = cls.extract_go_package_imports_and_code(task_code)
        _, ext_go_imports, ext_go_non_import_code = cls.extract_go_package_imports_and_code(task_extension)
        
        # Combine all imports, ensuring uniqueness
        go_imports.update(ext_go_imports)
        all_imports = "import (\n" + "\n".join(sorted(f'\t"{imp}"' for imp in go_imports)) + "\n)"
        
        # Combine the non-import code sections
        combined_code = go_non_import_code + "\n" + ext_go_non_import_code
        
        # Ensure proper ordering of Go code, avoiding duplicate package declarations
        full_go_code = f"{package_declaration}\n\n{all_imports}\n\n{combined_code}"
        return cls.run_language_task(
            language="go",
            task_requirements=task_requirements,
            task_code=full_go_code,
            args=args,
            task_extension=task_extension,
            installer=TaskInstallers.install_go_modules,
            interpreter_command="go run ./task_code.go",
            file_extension=".go",
            compile_required=False
        )

    @classmethod
    def run_rust_task(cls, task_requirements, task_code, args, task_extension):
        return cls.run_language_task(
            language="rust",
            task_requirements=task_requirements,
            task_code=task_code,
            args=args,
            task_extension=task_extension,
            installer=TaskInstallers.install_rust_crates,
            interpreter_command=lambda cargo_toml_path: f"cargo build --manifest-path {cargo_toml_path} && ./target/debug/temporary_package",
            file_extension=".rs",
            setup_project_structure=cls.setup_rust_project_structure,
            compile_required=True
        )

    @classmethod
    def run_java_task(cls, task_requirements, task_code, args, task_extension):
        # Integrate task_code into the TaskCode class within task_extension
        combined_code = cls.combine_code_and_extension(task_code, task_extension)

        return cls.run_language_task(
            language="java",
            task_requirements=task_requirements,
            task_code=combined_code,  # Combined code is passed here
            args=args,
            task_extension="",  # No separate task_extension since it is already combined
            installer=TaskInstallers.install_java_dependencies,
            interpreter_command="javac task_code.java && java TaskCode",  # Ensure consistent naming
            file_extension=".java",
            compile_required=True
        )

    @classmethod
    def run_java_task(cls, task_requirements, task_code, args, task_extension):
        # Extract imports and method definitions from the provided task_code
        task_code_lines = task_code.strip().splitlines()
        imports = set()
        method_lines = []

        for line in task_code_lines:
            if line.strip().startswith("import "):
                imports.add(line.strip())
            else:
                method_lines.append(line.strip())

        # Ensure imports are unique and properly ordered
        all_imports = "\n".join(sorted(imports))

        # Combine imports and method definitions into a cleaned task_code
        task_code_cleaned = "\n".join(method_lines)

        # Inject the cleaned method code into the TaskCode class by replacing the placeholder
        task_extension = task_extension.replace("/*METHOD_PLACEHOLDER*/", task_code_cleaned)

        # Ensure all imports are at the top of the file
        task_extension = all_imports + "\n\n" + task_extension

        return cls.run_language_task(
            language="java",
            task_requirements=task_requirements,
            task_code=task_extension,
            args=args,
            task_extension="",
            installer=TaskInstallers.install_java_dependencies,
            interpreter_command="javac task_code.java && java TaskCode",
            file_extension=".java",
            compile_required=True
        )

    @classmethod
    def combine_code_and_extension(cls, task_code, task_extension):
        # Extract imports and code from both task_code and task_extension
        imports, non_import_code = cls.extract_imports_and_code(task_code)
        ext_imports, non_import_extension = cls.extract_imports_and_code(task_extension)

        # Combine all imports at the top, ensuring uniqueness
        all_imports = "\n".join(sorted(imports.union(ext_imports)))

        # Combine the task_code and task_extension inside the TaskCode class
        combined_code = f"""
{all_imports}

public class TaskCode {{
{non_import_code}

{non_import_extension}
}}
"""

        return combined_code

    @classmethod
    def extract_imports_and_code(cls, code):
        """Extract import statements and the rest of the code separately."""
        imports = set()
        non_import_code = []

        for line in code.splitlines():
            if line.strip().startswith("import "):
                imports.add(line.strip())
            else:
                non_import_code.append(line)

        return imports, "\n".join(non_import_code)


    @classmethod
    def extract_go_package_imports_and_code(cls, code):
        """Extract Go package declaration, import statements, and the rest of the code separately."""
        imports = set()
        non_import_code = []
        package_declaration = None
        in_import_block = False

        for line in code.splitlines():
            stripped_line = line.strip()

            if stripped_line.startswith("package "):
                if not package_declaration:
                    package_declaration = line.strip()
            elif stripped_line.startswith("import "):
                in_import_block = True
                # Single-line import statement or start of multi-line import block
                if stripped_line.startswith("import ("):
                    continue  # Start of a multi-line import block
                elif stripped_line.startswith("import \""):
                    imports.add(stripped_line.replace("import", "").strip().replace("\"", ""))
                else:
                    in_import_block = False
                    non_import_code.append(line)
            elif in_import_block:
                # Inside a multi-line import block
                if stripped_line == ")":
                    in_import_block = False
                else:
                    imports.add(stripped_line.replace("\"", "").strip())
            else:
                non_import_code.append(line)

        # Ensure a package declaration exists
        if not package_declaration:
            package_declaration = "package main"

        return package_declaration, imports, "\n".join(non_import_code)

    @classmethod
    def run_language_task(cls, language, task_requirements, task_code, args, task_extension, installer, interpreter_command, file_extension, setup_project_structure=None, compile_required=False):
        try:
            temp_dir = tempfile.mkdtemp()
            print(temp_dir)
            if setup_project_structure:
                setup_project_structure(temp_dir, task_code, task_extension, task_requirements)
            else:
                cls.setup_generic_project_structure(temp_dir, task_code, task_extension, file_extension)
            temp_dir_with_deps = installer(temp_dir, task_requirements)
            if not temp_dir_with_deps:
                return {
                    "error": "PackageInstallationError",
                    "error_message": f"Failed to install one or more packages for {file_extension}."
                }
            return cls.run_generic_task(
                language=language,
                task_code=task_code,
                args=args,
                interpreter_command=interpreter_command,
                file_extension=file_extension,
                temp_dir=temp_dir,
                task_extension=task_extension,
                compile_required=compile_required
            )

        except Exception as e:
            return {
                "error": str(e),
                "error_message": f"An error occurred while executing the task.",
                "traceback": traceback.format_exc()
            }

    @classmethod
    def setup_generic_project_structure(cls, temp_dir, task_code, task_extension, file_extension):
        # Ensure the temporary directory exists (though it should already be created by the caller)
        os.makedirs(temp_dir, exist_ok=True)
        temp_code_file_path = os.path.join(temp_dir, f"task_code{file_extension}")

        with open(temp_code_file_path, 'w') as temp_code_file:
            temp_code_file.write(task_code)
            temp_code_file.write("\n")
            temp_code_file.write(task_extension)

    @classmethod
    def setup_rust_project_structure(cls, temp_dir, task_code, task_extension, task_requirements):
        # Create the src directory and main.rs file
        src_dir = os.path.join(temp_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        main_rs_path = os.path.join(src_dir, "main.rs")

        with open(main_rs_path, 'w') as main_rs_file:
            main_rs_file.write(task_code)
            main_rs_file.write("\n")
            main_rs_file.write(task_extension)

    @classmethod
    def parsed_output(cls, output):
        parsers = [
            lambda o: json.loads(o.split(DEMARCATION)[-1]),
            lambda o: json.loads(o),
            lambda o: json.loads(o.split("\n")[-1])
        ]
        for parse in parsers:
            try:
                return parse(output)
            except:
                continue
        return output

    @classmethod
    def run_generic_task(cls, language, task_code, args, interpreter_command, file_extension, temp_dir, task_extension, compile_required=False):
        try:
            start_time = time.perf_counter_ns()

            # Ensure the temporary directory exists (though it should already be created by the caller)
            os.makedirs(temp_dir, exist_ok=True)

            # Create the full path to the code file within the temporary directory
            temp_code_file_path = os.path.join(temp_dir, f"task_code{file_extension}")
            # Write the task code to the file within the temporary directory
            with open(temp_code_file_path, 'w') as temp_code_file:
                temp_code_file.write(task_code)
                temp_code_file.write("\n")
                if language != "go":
                    temp_code_file.write(task_extension)

            args_json = json.dumps(args)
            if compile_required:
                # Dynamically determine the command if interpreter_command is a lambda
                if language == "rust":
                    cargo_toml_path = os.path.join(temp_dir, "Cargo.toml")
                    interpreter_command = interpreter_command(cargo_toml_path)

                compile_command, run_command = interpreter_command.split("&&")
                compile_command = compile_command.strip().split()
                run_command = run_command.strip().split()

                compile_process = subprocess.run(compile_command, capture_output=True, text=True, cwd=temp_dir)
                if compile_process.returncode != 0:
                    return {
                        "error": "CompilationError",
                        "error_message": f"Compilation failed with exit code {compile_process.returncode}",
                        "error_details": compile_process.stderr
                    }
                command = run_command + [args_json]
            elif language == 'go':
                command = interpreter_command.split()
            else:
                command = interpreter_command.split() + [temp_code_file_path]
            # else:
            #     command = interpreter_command.split() + [temp_code_file_path, args_json]
            result = subprocess.run(command, cwd=temp_dir, capture_output=True, text=True)

            end_time = time.perf_counter_ns()
            execution_time_microseconds = (end_time - start_time) / 1000
            if result.returncode != 0:
                return {
                    "error": "ExecutionError",
                    "error_message": f"Subprocess returned non-zero exit code {result.returncode}",
                    "error_details": result.stderr
                }

            output = result.stdout.strip()
            return {
                "output": TaskRunners.parsed_output(output),
                "execution_length": execution_time_microseconds,
            }
        except Exception as e:
            return {
                "error": str(e),
                "error_message": f"An error occurred while executing the task with {interpreter_command}.",
                "traceback": traceback.format_exc()
            }

