# Workbench

## About

This directory holds an example set up for working with JSON-LD files, loading them 
to a triplestore and doing test queries and other operations on those triples.

It is only an example of what such a working environment might look like.  Such 
environment are highly personal and often need to change to adjust to a given user or 
environment.  

This is ment only as an example and tools like those listed in the
[tooling document](../docs/tooling.md) could be included or exchanged for those used here.


## This workbench

* Scripts (bash)
* Oxigraph as the server, 
* Graph Notebook
* Graph Explorer 

### Scripts

### Oxigraph

  * can run as docker or via cargo, see: https://crates.io/crates/oxigraph_server#installation
  * ```podman run --group-add keep-groups --privileged --rm -v $PWD/data:/data -p 7878:7878 ghcr.io/oxigraph/oxigraph --location /data serve --bind 0.0.0.0:7878  ```

### Graph Notebook

[AWS Graph Notebook](https://github.com/aws/graph-notebook)

* enter your virtual env
* python -m graph_notebook.start_jupyterlab --jupyter-dir  .

### Graph Explorer

[AWS Graph Explore](https://github.com/aws/graph-explorer)

  * Must run on 80 and 443 for podman you will likely need to allow this with: 
    * ```sudo sysctl net.ipv4.ip_unprivileged_port_start=80```
