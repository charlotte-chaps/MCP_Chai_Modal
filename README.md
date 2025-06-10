---
title: MCP Modal Protein Folding
emoji: 🧬
colorFrom: gray
colorTo: green
sdk: gradio
sdk_version: 5.33.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: MCP server to simulate protein folding on Modal cluster
tags: 
   - mcp-server-track
   - Modal Labs Choice Award
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

### Environment creation with uv
Run the following in a bash shell:
```bash
uv venv 
source .venv/bin/activate
uv pip install gradio[mcp] modal gemmi gradio_molecule3d 
```

### Run the app 
Run in a bash shell: 
```bash
gradio app.py
```
