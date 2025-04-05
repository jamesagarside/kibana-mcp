import subprocess
import yaml
import sys

# Assuming utils.py is in the same directory
from .utils import print_info, print_error, print_warning, command_exists

# ==============================================================================
# --- Docker Management ---
# ==============================================================================
def get_docker_compose_cmd():
    """Determines whether to use 'docker compose' or 'docker-compose'"""
    try:
        # Check V2 first
        subprocess.run(["docker", "compose", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print_info("Using Docker Compose V2 ('docker compose')")
        return ["docker", "compose"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        if command_exists("docker-compose"):
            print_info("Using Docker Compose V1 ('docker-compose')")
            return ["docker-compose"]
        else:
            return None

def run_compose_command(compose_file_path, compose_cmd_base, *args):
    """Runs a docker compose command."""
    cmd = compose_cmd_base + ["-f", str(compose_file_path)] + list(args)
    print_info(f"Running: {' '.join(cmd)}")
    try:
        # Use run instead of Popen for simpler commands, capture output if needed
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print_info(f"Command successful:")
        if result.stdout:
            print(result.stdout) # Print stdout on a new line if it exists
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Docker Compose command failed: {' '.join(cmd)}")
        print_error(f"Stderr:\n{e.stderr}")
        print_error(f"Stdout:\n{e.stdout}")
        return False
    except Exception as e:
        print_error(f"An unexpected error occurred running compose: {e}")
        return False

def parse_compose_config(compose_file_path):
    """Parses docker-compose.yml to extract ports and password."""
    config = {"es_port": "9200", "kibana_port": "5601", "es_password": "elastic"}
    try:
        with open(compose_file_path, 'r') as f:
            compose_data = yaml.safe_load(f)

        # Extract Elasticsearch port
        es_ports = compose_data.get('services', {}).get('elasticsearch', {}).get('ports', [])
        for port_mapping in es_ports:
            if str(port_mapping).endswith(":9200"):
                config["es_port"] = str(port_mapping).split(":")[0].strip('"')
                break

        # Extract Kibana port
        kibana_ports = compose_data.get('services', {}).get('kibana', {}).get('ports', [])
        for port_mapping in kibana_ports:
            if str(port_mapping).endswith(":5601"):
                config["kibana_port"] = str(port_mapping).split(":")[0].strip('"')
                break

        # Extract Elasticsearch password
        es_env = compose_data.get('services', {}).get('elasticsearch', {}).get('environment', {})
        # Handle both list and dict formats for environment variables
        if isinstance(es_env, list):
            for env_var in es_env:
                if env_var.startswith("ELASTIC_PASSWORD="):
                    config["es_password"] = env_var.split("=", 1)[1].strip('"')
                    break
        elif isinstance(es_env, dict):
             config["es_password"] = es_env.get("ELASTIC_PASSWORD", config["es_password"])

    except FileNotFoundError:
        print_error(f"Compose file not found at {compose_file_path}")
        sys.exit(1)
    except Exception as e:
        print_warning(f"Could not parse {compose_file_path}: {e}. Using defaults.")

    print_info(f"Parsed config: Ports(ES:{config['es_port']}, Kibana:{config['kibana_port']}), Password:{config['es_password']}")
    return config 