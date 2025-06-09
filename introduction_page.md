<style>
code[class*="language-bash"], pre[class*="language-bash"] {
  background: #fff !important;
}
</style>

# Stakes

The industry is being deeply changed by the development of LLMs and the recent possibilities to provide them access to external tools. For years, companies have used simulation tools to accelerate and reduce the cost of product development. One of the main challenges in the coming years will be to create agents that can set up, run, and process simulations to further accelerate innovation.

# Objective

This project is a first step in creating AI agents that perform simulations on existing software. Key domains include:
- **CFD** (Computational Fluid Dynamics) simulations
- **Biology** (Protein Folding, Molecular Dynamics, etc.)
- **Neural network applications**

> This project focuses on protein folding, but the same principles can be applied to other domains.

Industrial computations are often performed on HPC clusters with large resources, so simulations typically run on separate servers. The LLM must be able to access simulation results to provide complete answers to users.

## Modal
[Modal](https://modal.com/) is a serverless platform that provides a simple way to run any application with the latest CPU and GPU hardware.

## Chai-1 Model
[Chai-1](https://www.chaidiscovery.com/blog/introducing-chai-1) is a multi-modal foundation model for molecular structure prediction, performing at state-of-the-art levels across a variety of benchmarks. Chai-1 enables unified prediction of proteins, small molecules, DNA, RNA, glycosylations, and more. Using Chai-1 on Modal is a great example of running folding simulations.

---

# Instructions

<div style="background-color:#f5f5f5; border-radius:8px; padding:18px 24px; margin-bottom:24px; border:1px solid #cccccc;">

### 1. <span style="color:#2563eb;">(Optional) Create your JSON configuration file</span>
<small>Default configuration is available if you skip this step.</small>

- Set your simulation parameters and generate the JSON config file. A unique identifier will be assigned (e.g., `chai_{run_id}_config.json`).
- **Parameters:**
  - <b>Number of diffusion time steps:</b> 1 to 500
  - <b>Number of trunk recycles:</b> 1 to 5
  - <b>Seed:</b> 1 to 100
  - <b>ESM_embeddings:</b> Include or not
  - <b>MSA_server:</b> Include or not

### 2. <span style="color:#2563eb;">(Optional) Upload a FASTA file with your molecule sequence</span>
<small>Default FASTA files are available if you skip this step.</small>

- Write your FASTA content and create the file. A unique identifier will be assigned (e.g., `chai_{run_id}_input.fasta`).
- <b style="color:#b91c1c;">Warning:</b> The header must be well formatted for Chai1 to process it.

**FASTA template:**
```fasta
>{molecule_type}|{molecule_name}
Sequence (for protein/RNA/DNA) or SMILES for ligand
```

**Accepted  molecule types:** 
 `protein`/ `rna`/  `dna` / `ligand`

**Default input (provided by Chai1):**
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
<small>For a peptide, use `protein` as the molecule type.</small>

**Other example:**
```fasta
>protein|lysozyme
MNIFEMLRIDEGLRLKIYKDTEGYYTIGIGHLLTKSPDLNAAKSELDKAIGRNCNGVITKDEAEKLFNQDVDAAVRGILRNAKLKPVYDSLDAVRRCAAINQVFQMGETGVAGFTNSLRMLQQKRWDEAAVNLAKSRWYNQTPDRAKRVITTFRTGTWDAYKNL
```
### 3. <span style="color:#2563eb;">Select your config and FASTA files</span>
<small>Files are stored in your working directory as you create them.</small>

### 4. <span style="color:#2563eb;">Click the "Run" button to start the simulation</span>

### 5. <span style="color:#2563eb;">View the 3D visualization of your molecule</span>
</div>


# Work Performed
This interface allows you to run Chai1 simulations on a given FASTA sequence file. The Chai1 model predicts the 3D structure of proteins based on their amino acid sequences. You can input a FASTA file containing the sequence of the molecule you want to simulate, and the output will be a 3D representation of the molecule based on the Chai1 model.

# Disclaimer
This interface is for educational and research purposes only. Results may vary based on the input sequence and the Chai1 model's capabilities.

# Contact
For any issues or questions, please contact the developer or refer to the documentation.
