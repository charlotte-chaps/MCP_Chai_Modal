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


# Stakes
The industry is undergoing a profound transformation due to the development of Large Language Models (LLMs) and the recent advancements that enable them to access external tools. 
For years, companies have leveraged simulation tools to accelerate and reduce the costs of product development. 
One of the primary challenges in the coming years will be to create agents capable of setting up, running, and processing simulations to further expedite innovation.
Engineers will focus on analysis rather than simulation setup, allowing them to concentrate on the most critical aspects of their work.

# Objective

This project represents a first step towards developing AI agents that can perform simulations using existing engineering softwares. 
Key domains of application include:
- **CFD** (Computational Fluid Dynamics) simulations
- **Biology** (Protein Folding, Molecular Dynamics, etc.)
- **Neural network applications**

While this project focuses on biomolecules folding, the principles employed can be extended to other domains. 
Specifically, it utilizes [Chai-1](https://www.chaidiscovery.com/blog/introducing-chai-1), a multi-modal foundation model for molecular structure prediction that achieves state-of-the-art performance across various benchmarks. 
Chai-1 enables unified prediction of proteins, small molecules, DNA, RNA, glycosylations, and more. 

Industrial computations are frequently performed on High-Performance Computing (HPC) clusters with substantial resources, necessitating that simulations typically run on separate servers. 
To provide comprehensive answers to users, the LLM must be able to access simulation results. To this end, [Modal Labs](https://modal.com/), a serverless platform that offers a straightforward method to run any application with the latest CPU and GPU hardware, will be used.

# Benefits

1. **Efficiency**: The MCP server's connected to high-performance computing capabilities ensure that simulations are run quickly and efficiently.

2. **Ease of Use**: Only provide necessary parameters to the user to simplify the process of setting up and running complex simulations.

3. **Integration**: The seamless integration between the LLM's chat interface and the MCP server allows for a streamlined workflow, from simulation setup to results analysis.

The following video illustrates a practical use of the MCP server to run a biomolecules folding simulation using the Chai-1 model. 
In this scenario, Copilot is used in Agent mode with Claude 3.5 Sonnet to leverage the tools provided by the MCP server.

# MCP tools
1. `create_fasta_file`: Create a FASTA file from a biomolecule sequence string with a unique name.
2. `create_json_config`: Create a JSON configuration file from the Gradio interface inputs.
3. `compute_Chai1`: Compute a Chai-1 simulation on Modal labs server. Return a DataFrame with predicted scores: aggregated, pTM and ipTM.
4. `plot_protein`: Plot the 3D structure of a biomolecule using the DataFrame from `compute_Chai1` (Use for Gradio interface).
5. `show_cif_file`: Plot a 3D structure from a CIF file with the Molecule3D library (Use for the Gradio interface).

 # Result example
The following image shows an example of a protein folding simulation using the Chai-1 model. 
The simulation was run with the default configuration and the image is 3D view from the Gradio interface.

![Protein folding example](images/protein.png)


 # What's next?
1. Expose additional tools to post-process the results of the simulations. 
The current post-processong tools are suited for the Gradio interface (ex: Plot images of the molecule structure from a file).
2. Continue the pipeline by adding softawres like [OpenMM](https://openmm.org/) or [Gromacs](https://www.gromacs.org/) for molecular dynamics simulations.
3. Perform complete simulation plans including loops over parameters fully automated by the LLM.

# Contact
For any issues or questions, please contact the developer or refer to the documentation.>


# Environment creation with uv
Run the following in a bash shell:
```bash
uv venv 
source .venv/bin/activate
uv pip install gradio[mcp] modal gemmi gradio_molecule3d 
```

# Run the app 
Run in a bash shell: 
```bash
gradio app.py
```

# Gradio interface instructions

<div style="background-color:#f5f5f5; border-radius:8px; padding:18px 24px; margin-bottom:24px; border:1px solid #cccccc;">

### 1. <span style="color:#e98935;">Create your JSON configuration file (Optional)</span>
<small>Default configuration is available if you skip this step.</small>

- In the `Configuration 📦` window, set your simulation parameters and generate the JSON config file. You can provide a file name in the dedicated box that will appear in the list of available configuration files. If you don't, a unique identifier will be assigned (e.g., `chai_{unique_id}_config.json`).
- **Parameters:**
  - <b>Number of diffusion time steps:</b> 1 to 500
  - <b>Number of trunk recycles:</b> 1 to 5
  - <b>Seed:</b> 1 to 100
  - <b>ESM_embeddings:</b> Include or not
  - <b>MSA_server:</b> Include or not

### 2. <span style="color:#e98935;">Upload a FASTA file with your molecule sequence (Optional)</span>
<small>Default FASTA files are available if you skip this step.</small>

- In the `Configuration 📦` window, write your FASTA content and create the file. You can provide a file name in the dedicated box that will appear in the list of available configuration files. If you don't provide a file name a unique identifier will be assigned (e.g., `chai_{unique_id}_input.fasta`). Also, if you don't provide a fasta content a default sequence will be written in the file.
- <b style="color:#b91c1c;">Warning:</b> The header must be well formatted for Chai1 to process it.

**FASTA template:**
<div style="background-color:#ffffff; border-radius:8px; padding:18px 24px; margin-bottom:24px; border:1px solid #cccccc;">

```fasta
>{molecule_type}|{molecule_name}
Sequence (for protein/RNA/DNA) or SMILES for ligand
```

</div>

**Accepted  molecule types:** 
 `protein`/ `rna`/  `dna` / `ligand`

**Default input (provided by Chai1):**
<div style="background-color:#ffffff; border-radius:8px; padding:18px 24px; margin-bottom:24px; border:1px solid #cccccc;">

```fasta
>protein|name=example-of-long-protein
AGSHSMRYFSTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASPRGEPRAPWVEQEGPEYWDRETQKYKRQAQTDRVSLRNLRGYYNQSEAGSHTLQWMFGCDLGPDGRLLRGYDQSAYDGKDYIALNEDLRSWTAADTAAQITQRKWEAAREAEQRRAYLEGTCVEWLRRYLENGKETLQRAEHPKTHVTHHPVSDHEATLRCWALGFYPAEITLTWQWDGEDQTQDTELVETRPAGDGTFQKWAAVVVPSGEEQRYTCHVQHEGLPEPLTLRWEP

>protein|name=example-of-short-protein
AIQRTPKIQVYSRHPAENGKSNFLNCYVSGFHPSDIEVDLLKNGERIEKVEHSDLSFSKDWSFYLLYYTEFTPTEKDEYACRVNHVTLSQPKIVKWDRDM

>protein|name=example-peptide
GAAL

>ligand|name=example-ligand-as-smiles
CCCCCCCCCCCCCC(=O)O
```

</div>
<small>For a peptide, use `protein` as the molecule type.</small>

**Other example:**
<div style="background-color:#ffffff; border-radius:8px; padding:18px 24px; margin-bottom:24px; border:1px solid #cccccc;">

```fasta
>protein|lysozyme
MNIFEMLRIDEGLRLKIYKDTEGYYTIGIGHLLTKSPDLNAAKSELDKAIGRNCNGVITKDEAEKLFNQDVDAAVRGILRNAKLKPVYDSLDAVRRCAAINQVFQMGETGVAGFTNSLRMLQQKRWDEAAVNLAKSRWYNQTPDRAKRVITTFRTGTWDAYKNL
```

```fasta
>rna|Chain B
UUAGGCGGCCACAGCGGUGGGGUUGCCUCCCGUACCCAUCCCGAACACGGAAGAUAAGCCCACCAGCGUUCCGGGGAGUACUGGAGUGCGCGAGCCUCUGGGAAACCCGGUUCGCCGCCACC
MNIFEMLRIDEGLRLKIYKDTEGYYTIGIGHLLTKSPDLNAAKSELDKAIGRNCNGVITKDEAEKLFNQDVDAAVRGILRNAKLKPVYDSLDAVRRCAAINQVFQMGETGVAGFTNSLRMLQQKRWDEAAVNLAKSRWYNQTPDRAKRVITTFRTGTWDAYKNL
```

</div>

### 3. <span style="color:#e98935;">Select your config and FASTA files</span>
<small>Files are stored in your working directory as you create them.</small>

In the `Run folding simulation 🚀` window, refresh the file list by clicking on the `Refresh available files`. Then select the configuration and fasta file you want.

### 4. <span style="color:#e98935;">Run the simulation</span>

Press the `Run Simulation` button to start de folding Simulation. Five proteins folding simulations will be performed. This parameter is hard coded in Chai-1. The simulation time is expected to be from 2min to 10min depending on the molecule.

### 5. <span style="color:#e98935;">Analyse the results of your simulation</span>

To analyse the results of the simulation, two outputs are provided:
- A table showing the score of the 5 folding performed
- Interactive 3D visualization of the molecule

Finally, you can get to the `Plot CIF file 💻` window to watch the cif files. This is mainly used to visualize CIF files after using this tool as an MCP server.

