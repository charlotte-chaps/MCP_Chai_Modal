<style>
code[class*="language-bash"], pre[class*="language-bash"] {
  background: #fff !important;
}
</style>

---

# Instructions

<div style="background-color:#f5f5f5; border-radius:8px; padding:18px 24px; margin-bottom:24px; border:1px solid #cccccc;">

### 1. <span style="color:#e98935;">Create your JSON configuration file (Optional)</span>
<small>Default configuration is available if you skip this step.</small>

- In the `Configuration 📦` window, set your simulation parameters and generate the JSON config file. You can provide a file name in the dedicated box that will appear in the list of available configuration files. If you don't, a unique identifier will be assigned (e.g., `chai_{run_id}_config.json`).
- **Parameters:**
  - <b>Number of diffusion time steps:</b> 1 to 500
  - <b>Number of trunk recycles:</b> 1 to 5
  - <b>Seed:</b> 1 to 100
  - <b>ESM_embeddings:</b> Include or not
  - <b>MSA_server:</b> Include or not

### 2. <span style="color:#e98935;">Upload a FASTA file with your molecule sequence (Optional)</span>
<small>Default FASTA files are available if you skip this step.</small>

- In the `Configuration 📦` window, write your FASTA content and create the file. You can provide a file name in the dedicated box that will appear in the list of available configuration files. If you don't provide a file name a unique identifier will be assigned (e.g., `chai_{run_id}_input.fasta`). Also, if you don't provide a fasta content a default sequence will be written in the file.
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

</div>

### 3. <span style="color:#e98935;">Select your config and FASTA files</span>
<small>Files are stored in your working directory as you create them.</small>

In the `Run folding simulation 🚀` window, refresh the file list by clicking on the `Refresh available files`. Then select the configuration and fasta file you want.

### 4. <span style="color:#e98935;">Run the simulation</span>

Press the `Run Simulation` button to start de folding Simulation. Five protein folding simulations will be performed. Unfortunately, this parameter is hard coded in Chai-1. The simulation time is expected to be from 2min to 10min depending on the molecule.

### 5. <span style="color:#e98935;">Analyse the results of your simulation</span>

To analyse the results of the simulation, two outputs are provided:
- A table showing the score of the 5 folding performed
- Interactive 3D visualization of the molecule

Finally, you can get to the `Show molecule from a CIF file 💻` window to watch the cif files. This is mainly used to visualize CIF files after using this tool as an MCP server.

</div>