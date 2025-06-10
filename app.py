# Import librairies
from pathlib import Path
from typing import Optional
from uuid import uuid4
import hashlib
import json
import gradio as gr
import gemmi
from gradio_molecule3d import Molecule3D
from modal_app import app, chai1_inference, download_inference_dependencies, here
from numpy import load
from typing import List

theme = gr.themes.Default(
    text_size="md",
    radius_size="lg",
)

# Helper functions
def select_best_model(
    run_id: str,
    number_of_scores: int=5,
    scores_to_print: List[str]=None,
    results_dir: str="results/score",
    prefix: str="-scores.model_idx_",
):
    """
    Selects the best model based on the aggregate score among several simulation results.

    Args:
        run_id (str): Unique identifier for the inference run.
        number_of_scores (int, optional): Number of models to evaluate (number of score files to read). Default is 5.
        scores_to_print (List[str], optional): List of score names to display for each model (e.g., ["aggregate_score", "ptm", "iptm"]). Default is ["aggregate_score", "ptm", "iptm"].
        results_dir (str, optional): Directory where the result files are located. Default is "results/score".
        prefix (str, optional): Prefix used in the score file names. Default is "-scores.model_idx_".

    Returns:
        Tuple[int, float]: 
            - best_model (int): Index of the best model (the one with the highest aggregate score and without inter-chain clashes).
            - max_aggregate_score (float): Value of the highest aggregate score.
    """
    print(f"🧬 Start reading scores for each inference...")
    if scores_to_print is None:
        scores_to_print = ["aggregate_score", "ptm", "iptm"]
    max_aggregate_score = 0
    best_model = None
    for model_index in range(number_of_scores):
        print(f"    🧬 Reading scores for model {model_index}...")
        data = load(f"{results_dir}/{run_id}{prefix}{model_index}.npz")
        if data["has_inter_chain_clashes"][0] == False:
            for item in scores_to_print:
                print(f"{item}: {data[item][0]}")
        else:
            print(f"        🧬 Model {model_index} has inter-chain clashes, skipping scores.")
            continue
        if data["aggregate_score"][0] > max_aggregate_score:
            max_aggregate_score = data["aggregate_score"][0]
            best_model = int(model_index)
    print(
        f"🧬 Best model is {best_model} with an aggregate score of {max_aggregate_score}."
    )
    return best_model, max_aggregate_score

# Definition of the tools for the MCP server 
# Function to return a fasta file
def create_fasta_file(file_content: str, name: Optional[str] = None, seq_name: Optional[str] = None) -> str:
    """Create a FASTA file from a biomolecule sequence string with a unique name.
    
    Args:
        file_content (str): The content of the FASTA file required with optional line breaks
        name (str, optional): FASTA file name ending with .fasta ideally. If not provided, a unique ID will be generated
        seq_name (str, optional): The name/identifier for the sequence. Defaults to "protein"
        
    
    Returns:
        str: Name of the created FASTA file
    """
    # If the file_content is empty, raise an error
    if not file_content.strip():
        print("Fasta file content cannot be empty so the example fasta file will be used")
        file_content = ">protein|name=example-protein\nAGSHSMRYFSTSVSRPGRGEPRFIAVGYVDDTQFVRFD"
    
    # Remove any trailing/leading whitespace but preserve line breaks
    lines = file_content.strip().split('\n')
    
    # Check if the first line is a FASTA header
    if not lines[0].startswith('>'):
        # If no header provided, add one
        if seq_name is None:
            seq_name = "protein"
        file_content = f">{seq_name}\n{file_content}"
    
    # Create FASTA content (preserving line breaks)
    fasta_content = file_content
    
    # Generate a unique file name
    unique_id = hashlib.sha256(uuid4().bytes).hexdigest()[:8]
    if name:
        file_name = name
    else:
        file_name = f"chai1_{unique_id}.fasta"
    file_path = here / "inputs/fasta" / file_name
    
    # Write the FASTA file
    with open(file_path, "w") as f:
        f.write(fasta_content)


# Function to create a JSON file
def create_json_config(
    num_diffn_timesteps: int,
    num_trunk_recycles: int,
    seed: int,
    options: list,
    name: Optional[str] = None
    ) -> str:
    """Create a JSON configuration file from the Gradio interface inputs.
    
    Args:
        num_diffn_timesteps (int): Number of diffusion timesteps from slider
        num_trunk_recycles (int): Number of trunk recycles from slider
        seed (int): Random seed from slider
        options (list): List of selected options from checkbox group
        name (str, optional): JSON config file name ending with .json ideally. If not provided, a unique ID will be generated
    
    Returns:
        str: Name of the created JSON file
    """
    # Convert checkbox options to boolean flags
    use_esm_embeddings = "ESM_embeddings" in options
    use_msa_server = "MSA_server" in options
    
    # Create config dictionary
    config = {
        "num_trunk_recycles": num_trunk_recycles,
        "num_diffn_timesteps": num_diffn_timesteps,
        "seed": seed,
        "use_esm_embeddings": use_esm_embeddings,
        "use_msa_server": use_msa_server
    }
    
    # Generate file name based on provided name or unique ID
    unique_id = hashlib.sha256(uuid4().bytes).hexdigest()[:8]
    if name:
        file_name = name
    else:
        file_name = f"chai1_{unique_id}.json"
    file_path = here / "inputs/config" / file_name
    
    # Write the JSON file 
    with open(file_path, "w") as f:
        json.dump(config, f, indent=4)


# Function to compute Chai1 inference
def compute_Chai1(
    fasta_file_name: Optional[str] = "",
    inference_config_file_name: Optional[str] = "",
):
    """Compute a Chai1 simulation.

    Args:
        fasta_file_name (str, optional): FASTA file name to use for the Chai1 simulation.
            If not provided, uses the default input file.
        inference_config_file_name (str, optional): JSON configuration file name for inference.
            If not provided, uses the default quick inference configuration.

    Returns:
        pd.DataFrame: DataFrame containing model scores and CIF file paths
    """
    import pandas as pd
    with app.run():
        force_redownload = False
        
        print("🧬 checking inference dependencies")
        download_inference_dependencies.remote(force=force_redownload)

        # Define fasta file
        if not fasta_file_name:
            fasta_file_name = here / "inputs/fasta" / "chai1_default_input.fasta"   
        print(f"🧬 running Chai inference on {fasta_file_name}")
        fasta_file_name = here / "inputs/fasta" / fasta_file_name
        print(fasta_file_name)
        fasta_content = Path(fasta_file_name).read_text()

        # Define inference config file
        if not inference_config_file_name:
            inference_config_file_name = here / "inputs/config" / "chai1_quick_inference.json"
        inference_config_file_name = here / "inputs/config" / inference_config_file_name
        print(f"🧬 loading Chai inference config from {inference_config_file_name}")
        inference_config = json.loads(Path(inference_config_file_name).read_text())

        # Generate a unique run ID
        run_id = hashlib.sha256(uuid4().bytes).hexdigest()[:8]  # short id
        print(f"🧬 running inference with {run_id=}")

        results = chai1_inference.remote(fasta_content, inference_config, run_id)

        # Define output directory
        output_dir = Path("./results")
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"🧬 saving results to disk locally in {output_dir}")
        
        # Create lists to store data for DataFrame
        model_data = []
        
        for ii, (scores, cif) in enumerate(results):
            score_file = Path(output_dir, "score") / f"{run_id}-scores.model_idx_{ii}.npz"
            cif_file = Path(output_dir, "molecules") / f"{run_id}-preds.model_idx_{ii}.cif"
            
            score_file.write_bytes(scores)
            cif_file.write_text(cif)
            
            # Load score data
            data = load(str(score_file))
            
            if not data["has_inter_chain_clashes"][0]:
                model_data.append({
                    "Model Index": ii,
                    "Aggregate Score": float(data["aggregate_score"][0]),
                    "PTM": float(data["ptm"][0]),
                    "IPTM": float(data["iptm"][0]),
                    "CIF File": str(cif_file).split("/")[-1],  # Get just the file name
                })
        
        # Create DataFrame from collected data
        results_df = pd.DataFrame(model_data).sort_values("Aggregate Score", ascending=False)
        
        return results_df


# Function to plot the 3D protein structure
def plot_protein(result_df) -> str:
    """Plot the 3D structure of a biomolecule using the DataFrame from compute_Chai1.

    Args:
        result_df (pd.DataFrame): DataFrame containing model information and scores

    Returns:
        str: Path to the generated PDB file of the best model.
    """
    if result_df.empty:
        return ""  # Return empty string instead of None for type safety
    
    # Get the CIF file path of the model with highest aggregate score (already sorted)
    best_cif = str(Path("results/molecules") / result_df.iloc[0]["CIF File"])
    
    # Generate PDB file name
    pdb_file = best_cif.replace('.cif', '.pdb')
    
    # Convert CIF to PDB if it doesn't exist
    if not Path(pdb_file).exists():
        st = gemmi.read_structure(best_cif)
        st.write_minimal_pdb(pdb_file)
    
    return pdb_file


# Function to plot a CIF file
def show_cif_file(cif_file):
    """Plot a 3D structure from a CIF file with the Molecule3D library.

    Args:
        cif_file: A biomolecule structure file in CIF format. This can be a file uploaded by the user.
            If None, the function will return None.

    Returns:
        str or None: PDB file name if successful, None if no file was provided
            or if conversion failed.
    """
    if not cif_file:
        return None
    
    cif_path = Path(cif_file.name)
    st = gemmi.read_structure(str(cif_path))
    pdb_file = cif_path.with_suffix('.pdb')
    st.write_minimal_pdb(str(pdb_file))  # Convert PosixPath to string
    
    return str(pdb_file)


# Create the Gradio interface
reps = [{"model": 0,"style": "cartoon","color": "hydrophobicity"}]

with gr.Blocks(theme=theme) as demo:
    
    gr.Markdown(
    """
    # Protein Folding Simulation Interface
    This interface provides the tools to fold FASTA chains based on Chai-1 model. Also, this is a MCP server to provide all the tools to automate the process of folding biomolecules with LLMs.     
    """) 
    
    with gr.Tab("Introduction 🔭"):
        
        gr.Image("images/logo1.png", show_label=False, width=600, show_download_button=False, show_fullscreen_button=False, show_share_button=False)
        
        gr.Markdown(
        """
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
        
        The following video illustrates a practical use of the MCP server to run a biomolecule folding simulation using the Chai-1 model. 
        In this scenario, Copilot is used in Agent mode with Claude 3.5 Sonnet to leverage the tools provided by the MCP server.

        """
        )
        
        gr.HTML(
            """<style> 
                iframe { 
                display: block; 
                margin: 0 auto; 
            } 
            </style>
            <iframe width="600" height="338" 
            src="https://www.youtube.com/embed/P9cAKxJ9Zh8" 
            frameborder="0" allowfullscreen></iframe>""",
            label="MCP demonstration video"
        )
        
        gr.Markdown(
        """
        # MCP tools
        1. `create_fasta_file`: Create a FASTA file from a biomolecule sequence string with a unique name.
        2. `create_json_config`: Create a JSON configuration file from the Gradio interface inputs.
        3. `compute_Chai1`: Compute a Chai-1 simulation on Modal labs server. Return a DataFrame with protein scores.
        4. `plot_protein`: Plot the 3D structure of a biomolecule using the DataFrame from `compute_Chai1` (Use for Gradio interface).
        5. `show_cif_file`: Plot a 3D structure from a CIF file with the Molecule3D library (Use for the Gradio interface).
        """)
        
        with open("introduction_page.md", "r") as f:
            intro_md = f.read()
        gr.Markdown(intro_md)
        
        gr.Markdown(
        """
        # Result example
        The following image shows an example of a protein folding simulation using the Chai-1 model. 
        The simulation was run with the default configuration and the image is 3D view from the Gradio interface.
        """)    
        
        gr.Image("images/protein.png", show_label=True, width=400, label="Protein Folding example", show_download_button=False, show_fullscreen_button=False, show_share_button=False)
    
        gr.Markdown(
        """
        # What's next?
        1. Expose additional tools to post-process the results of the simulations. 
        The current post-processong tools are suited for the Gradio interface (ex: Plot images of the molecule structure from a file).
        2. Continue the pipeline by adding softawres like [OpenMM](https://openmm.org/) or [Gromacs](https://www.gromacs.org/) for molecular dynamics simulations.
        3. Perform complete simulation plans including loops over parameters fully automated by the LLM.
        
        # Contact
        For any issues or questions, please contact the developer or refer to the documentation.
        """)    

    
    with gr.Tab("Configuration 📦"):
        
        gr.Markdown(
        """        
        ## Fasta file and configuration generator (optional)
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                slider_nb = gr.Slider(1, 500, value=300, label="Number of diffusion time steps", info="Choose the number of diffusion time steps for the simulation", step=1, interactive=True, elem_id="num_iterations")
                slider_trunk = gr.Slider(1, 5, value=3, label="Number of trunk recycles", info="Choose the number of iterations for the simulation", step=1, interactive=True, elem_id="trunk_number")
                slider_seed = gr.Slider(1, 100, value=42, label="Seed", info="Choose the seed", step=1, interactive=True, elem_id="seed")
                check_options = gr.CheckboxGroup(["ESM_embeddings", "MSA_server"], value=["ESM_embeddings",], label="Additional options", info="Options to use ESM embeddings and MSA server", elem_id="options")
                config_name = gr.Textbox(placeholder="Enter a name for the json file (optional)", label="JSON file name")
                button_json = gr.Button("Create Config file")
                button_json.click(fn=create_json_config, inputs=[slider_nb, slider_trunk, slider_seed, check_options, config_name], outputs=[])
        
                
            with gr.Column(scale=1):   
                fasta_input = gr.Textbox(placeholder="Fasta format sequences", label="Fasta content", lines=10)
                fasta_name = gr.Textbox(placeholder="Enter the name of the fasta file name (optional)", label="Fasta file name")
                fasta_button = gr.Button("Create Fasta file")
                fasta_button.click(fn=create_fasta_file, inputs=[fasta_input, fasta_name], outputs=[])
                        
                gr.Markdown(
                """
                ## Example Fasta File
                ```
                >protein|name=example-protein
                AGSHSMRYFSTSVSRPGRGEPRFIAVGYVDDTQFVRFD      
                ```
                """)
       
       
    with gr.Tab("Run folding simulation 🚀"):     
        with gr.Row():                
            with gr.Column(scale=1):
                inp2 = gr.FileExplorer(root_dir=here / "inputs/config", 
                                value="chai1_default_inference.json",
                                label="Configuration file", 
                                file_count='single')    
                
            with gr.Column(scale=1):
                inp1 = gr.FileExplorer(root_dir=here / "inputs/fasta", 
                                value="chai1_default_input.fasta",
                                label="Input Fasta file", 
                                file_count='single')     
        btn_refresh = gr.Button("Refresh available files")
        
        # Only workaround I found to update the file explorer
        def update_file_explorer():
            """Don't need to be used by LLMs, but useful for the interface to update the file explorer"""
            return gr.FileExplorer(root_dir=here), gr.FileExplorer(root_dir=here)
        def update_file_explorer_2():
            """Don't need to be used by LLMs, but useful for the interface to update the file explorer"""
            return gr.FileExplorer(root_dir=here / "inputs/fasta"), gr.FileExplorer(root_dir=here / "inputs/config")
        
        btn_refresh.click(update_file_explorer, outputs=[inp1,inp2]).then(update_file_explorer_2, outputs=[inp1, inp2])
                      
        #out = Molecule3D(label="Plot the 3D Molecule", reps=reps)
        out = gr.DataFrame(
            headers=["Model Index", "Aggregate Score", "PTM", "IPTM", "CIF File"],
            datatype=["number", "number", "number", "number", "str"],
            label="Inference Results sorted by Aggregate Score",
            visible=True,
        )
        out2 = Molecule3D(label="Plot the 3D Molecule", reps=reps)
        
        btn = gr.Button("Run Simulation")
        btn.click(fn=compute_Chai1, inputs=[inp1 , inp2], outputs=[out]).then(
            fn=plot_protein, 
            inputs=out, 
            outputs=out2
        )
    
    
    with gr.Tab("Plot CIF file 💻"):     
        
        gr.Markdown(
        """
        ## Plot a 3D structure from a CIF file
        """)
        
        cif_input = gr.File(label="Input CIF file", file_count='single')
        cif_output = Molecule3D(label="Plot the 3D Molecule", reps=reps)        
        cif_input.change(fn=show_cif_file, inputs=cif_input, outputs=cif_output)

# Launch both the Gradio web interface and the MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=True)
