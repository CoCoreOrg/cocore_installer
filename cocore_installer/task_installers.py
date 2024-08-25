import os
import subprocess
import tempfile
import traceback
import sys

class TaskInstallers:
    @classmethod
    def install_python_packages(cls, temp_dir, task_requirements):
        try:
            # Path to the requirements.txt file within the temporary directory
            requirements_txt_path = os.path.join(temp_dir, "requirements.txt")
            # Write the task requirements to the requirements.txt file
            with open(requirements_txt_path, 'w') as req_file:
                req_file.write(task_requirements)
            # Install the packages using pip in the temporary directory
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_txt_path])
            # subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_txt_path, "--target", temp_dir])
            print("Packages from requirements.txt installed successfully.")
            return temp_dir
        except Exception as e:
            print(f"Failed to install packages from requirements.txt: {e}")
            print(traceback.format_exc())
            return None
    
    @classmethod
    def install_node_packages(cls, temp_dir, task_requirements):
        if task_requirements:
            try:
                # Path to the package.json file within the temporary directory
                package_json_path = os.path.join(temp_dir, "package.json")
                # Write the task requirements to the package.json file
                with open(package_json_path, 'w') as package_json_file:
                    package_json_file.write(task_requirements)
                # Run npm install in the temporary directory
                command = ["npm", "install", "--prefix", temp_dir, "--no-save"]
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Error installing Node.js packages: {result.stderr}")
                    return None
                return temp_dir
            except Exception as e:
                print(f"Error installing Node.js packages: {e}")
                return None
        return None
    
    @classmethod
    def install_ruby_gems(cls, temp_dir, task_requirements):
        if task_requirements:
            try:
                # Path to the Gemfile within the temporary directory
                gemfile_path = os.path.join(temp_dir, "Gemfile")
                # Write the task requirements to the Gemfile
                with open(gemfile_path, 'w') as gemfile:
                    gemfile.write('source "https://rubygems.org"\n')
                    gemfile.write(task_requirements)
                # Install the gems using bundle in the temporary directory
                # command = ["bundle", "install", "--gemfile", gemfile_path, "--path", os.path.join(temp_dir, "ruby_gems")]
                command = ["bundle", "install", "--gemfile", gemfile_path]
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Error installing Ruby gems: {result.stderr}")
                    return None
                return temp_dir
            except Exception as e:
                print(f"Error installing Ruby gems: {e}")
                return None
        return None
    
    @classmethod
    def install_go_modules(cls, temp_dir, task_requirements):
        if task_requirements:
            try:
                # Ensure the task_requirements contain a module declaration and Go version
                if "module" not in task_requirements:
                    cleaned = str.join("\n", ["\t"+e.strip() for e in task_requirements.split("\n")])
                    task_requirements = f"module temporary_package\n\nrequire (\n{cleaned}\n)"

                # Path to the go.mod file within the temporary directory
                go_mod_path = os.path.join(temp_dir, "go.mod")

                # Write the go.mod file
                with open(go_mod_path, 'w') as go_mod_file:
                    go_mod_file.write(task_requirements)

                # Run go mod tidy to ensure all dependencies are fetched
                command = ["go", "mod", "tidy", "-modfile", go_mod_path]
                result = subprocess.run(command, capture_output=True, text=True, cwd=temp_dir)
                if result.returncode != 0:
                    print(f"Error installing Go modules: {result.stderr}")
                    return None

                return temp_dir
            except Exception as e:
                print(f"Error installing Go modules: {e}")
                return None
        return None

    @classmethod
    def install_rust_crates(cls, temp_dir, task_requirements):
        if task_requirements:
            try:
                # Check for the presence of serde and serde_json
                has_serde = "serde" in task_requirements
                has_serde_json = "serde_json" in task_requirements

                # Add serde and/or serde_json if they are missing
                additional_dependencies = ""
                if not has_serde:
                    additional_dependencies += "serde = \"1.0\"\n"
                if not has_serde_json:
                    additional_dependencies += "serde_json = \"1.0\"\n"

                if additional_dependencies:
                    # If task_requirements already has [dependencies], append to it
                    if "[dependencies]" in task_requirements:
                        task_requirements += "\n" + additional_dependencies
                    else:
                        task_requirements = "[dependencies]\n" + additional_dependencies + task_requirements
                else:
                    # Ensure [dependencies] header is present
                    if "[dependencies]" not in task_requirements:
                        task_requirements = "[dependencies]\n" + task_requirements

                # Path to the Cargo.toml file within the temporary directory
                cargo_toml_content = f"""\
[package]
name = "temporary_package"
version = "0.1.0"
edition = "2021"

{task_requirements}

[[bin]]
name = "temporary_package"
path = "src/main.rs"
"""

                # Write the Cargo.toml file
                cargo_toml_path = os.path.join(temp_dir, "Cargo.toml")
                with open(cargo_toml_path, 'w') as cargo_toml_file:
                    cargo_toml_file.write(cargo_toml_content)

                return temp_dir
            except Exception as e:
                print(f"Error installing Rust crates: {e}")
                return None
        return None

    @classmethod
    def install_java_dependencies(cls, temp_dir, task_requirements):
        if task_requirements:
            try:
                # Base Jackson dependency
                jackson_dependency = """
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.12.3</version>
</dependency>
"""

                # Check if Jackson is already present in the task requirements
                if "com.fasterxml.jackson.core" not in task_requirements:
                    task_requirements += jackson_dependency

                # Base structure for the pom.xml file
                pom_xml_template = f"""
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>temporary_package</artifactId>
    <version>1.0-SNAPSHOT</version>

    <dependencies>
        {task_requirements.strip()}
    </dependencies>
</project>
"""

                # Write the pom.xml file
                pom_xml_path = os.path.join(temp_dir, "pom.xml")
                with open(pom_xml_path, 'w') as pom_xml_file:
                    pom_xml_file.write(pom_xml_template)

                # Install the Maven dependencies in the temporary directory
                command = ["mvn", "install", "-f", pom_xml_path]
                result = subprocess.run(command, capture_output=True, text=True, cwd=temp_dir)
                if result.returncode != 0:
                    print(f"Error installing Java dependencies: {result.stderr}")
                    return None
                return temp_dir
            except Exception as e:
                print(f"Error installing Java dependencies: {e}")
                return None
        return None
