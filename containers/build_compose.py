import argparse
import os
import re
import sys

def get_args():
    parser = argparse.ArgumentParser(
        description="Fill in Rabble docker-compose template")
    parser.add_argument("--template", default="docker-compose.tmpl.yml")
    parser.add_argument("--output", default="build_out/docker-compose.yml")
    return parser.parse_args()

def read_template(path):
    f = open(path)
    config = f.read()
    f.close()
    return config

def replace_vars(config, environ):
    pattern = re.compile(r"\[\[(.+?)\]\]")  # Matches: [[something]]
    variable_pairs = {}
    # Gather all required variables.
    for match in re.finditer(pattern, config):
        var_name = "RABBLE_" + match.group(1)
        if var_name not in environ:
            raise ValueError("Could not find env var: " + var_name)
        variable_pairs[match.group(0)] = environ[var_name]
    for var, value in variable_pairs.items():
        config = config.replace(var, value)
    return config

def write_config(config, path):
    f = open(path, "w")
    f.write(config)
    f.close()

def main():
    args = get_args()
    print("Generating Rabble docker-compose config:", args.output)
    config = read_template(args.template)
    out_config = replace_vars(config, os.environ)
    write_config(out_config, args.output)

if __name__ == '__main__':
    main()

