#!/usr/bin/env python3
"""
gengraph creates a directed graph of Rabble's GRPC service using graphviz.

gengraph should be run from the root of the rabble project directory, and requires
the python3 yaml & graphviz packages.

It writes generated files to the gengraph directory:
    - graph_output.gv: the graphviz source.
    - graph_output.gv.png: a picture generated using the graphviz source.

To change the engine used (it by default uses 'dot'), just change the ENGINE
variable in the top of the file. See https://graphviz.org for more details.

To render all versions, set ENGINE to "all".
To render none, set ENGINE to "".
"""
ENGINE = "all"

# dot - "hierarchical"
# neato - "spring model"
# fdp - "spring model''
# sfdp - multiscale version of fdp
# twopi - radial layouts
# circo - circular layout
ALL_ENGINES = ["dot", "neato", "fdp", "sfdp", "twopi", "circo"]

import subprocess
from collections import defaultdict

import yaml
from graphviz import Digraph

def get_env_mappings():
    with open("build_out/containers/first.yml") as f:
        yml = yaml.safe_load(f)

    mappings = defaultdict(list)
    services = yml['services']
    for service in services:
        if "environment" not in services[service]:
            continue
        for env in services[service]["environment"]:
            h, r = env.strip().split("=")
            if 'SERVICE_HOST' in h:
                mappings[service].append(r)
    return mappings

def render(envs, engine, use_engine_path=False):
    dot = Digraph(comment='Rabble Services', engine=engine)
    for service in envs:
        dot.node(service, service)
    for service in envs:
        for connection in envs[service]:
            dot.edge(service, connection)

    path = 'script/gengraph/graph_output.gv'
    if use_engine_path:
        path = 'script/gengraph/graph_output_{}.gv'.format(engine)

    if ENGINE != "":
        dot.render(path, format="png")

    return dot

def main():
    envs = get_env_mappings()

    if ENGINE != "all":
        dot = render(envs, ENGINE)
        print(dot.source)
        return

    for engine in ALL_ENGINES:
        render(envs, engine, use_engine_path=True)

if __name__ == "__main__":
    main()
