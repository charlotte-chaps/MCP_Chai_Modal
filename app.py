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
    text_size="lg",
    radius_size="lg",
)

# Definition of the tools for the MCP server 


def select_best_model(
    run_id: str,
    number_of_scores: int=5,
    scores_to_print: List[str]=None,
    results_dir: str="results",
    prefix: str="-scores.model_idx_",
):
    print(f"🧬 Start reading scores for each inference...")
    if scores_to_print is None:
        scores_to_print = ["aggregate_score", "ptm", "iptm"]
    max_aggregate_score = 0
    best_model = None
    for score in range(number_of_scores):
        print(f"    🧬 Reading scores for model {score}...")
        data = load(f"{results_dir}/{run_id}{prefix}{score}.npz")
        if data["has_inter_chain_clashes"][0] == False:
            for item in scores_to_print:
                print(f"{item}: {data[item][0]}")
        else:
            print(f"        🧬 Model {score} has inter-chain clashes, skipping scores.")
            continue
        if data["aggregate_score"][0] > max_aggregate_score:
            max_aggregate_score = data["aggregate_score"][0]
            best_model = int(score)
    print(
        f"🧬 Best model is {best_model} with an aggregate score of {max_aggregate_score}."
    )
    return best_model, max_aggregate_score


# Function to return a fasta file
def create_fasta_file(sequence: str, name: Optional[str] = None) -> str:
    """Create a FASTA file from a protein sequence string with a unique name.
    
    Args:
        sequence (str): The protein sequence string with optional line breaks
        name (str, optional): The name/identifier for the sequence. Defaults to "PROTEIN"
    
    Returns:
        str: Name of the created FASTA file
    """
    # Remove any trailing/leading whitespace but preserve line breaks
    lines = sequence.strip().split('\n')
    
    # Check if the first line is a FASTA header
    if not lines[0].startswith('>'):
        # If no header provided, add one
        if name is None:
            name = "PROTEIN"
        sequence = f">{name}\n{sequence}"
    
    # Create FASTA content (preserving line breaks)
    fasta_content = sequence
    
    # Generate a unique file name
    unique_id = hashlib.sha256(uuid4().bytes).hexdigest()[:8]
    file_name = f"chai1_{unique_id}_input.fasta"
    file_path = here / "inputs" / file_name
    
    # Write the FASTA file
    with open(file_path, "w") as f:
        f.write(fasta_content)
    
    return file_name


# Function to create a JSON file
def create_json_config(
    num_diffn_timesteps: int,
    num_trunk_recycles: int,
    seed: int,
    options: list
    ) -> str:
    """Create a JSON configuration file from the Gradio interface inputs.
    
    Args:
        num_diffn_timesteps (int): Number of diffusion timesteps from slider
        num_trunk_recycles (int): Number of trunk recycles from slider
        seed (int): Random seed from slider
        options (list): List of selected options from checkbox group
    
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
    
    # Generate a unique file name
    unique_id = hashlib.sha256(uuid4().bytes).hexdigest()[:8]
    file_name = f"chai1_{unique_id}_config.json"
    file_path = here / "inputs" / file_name
    
    # Write the JSON file
    with open(file_path, "w") as f:
        json.dump(config, f, indent=4)
    
    return file_name


# Function to compute Chai1 inference
def compute_Chai1(
    fasta_file: Optional[str] = "",
    inference_config_file: Optional[str] = "",
):
    """Compute a Chai1 simulation.

    Args:
        fasta_file (str, optional): FASTA file name containing the protein sequence.
            If not provided, uses the default input file.
        inference_config_file (str, optional): JSON configuration file name for inference.
            If not provided, uses the default quick inference configuration.

    Returns:
        str: Output PDB file name containing the predicted structure.
    """
    with app.run():
        
        force_redownload = False
        
        print("🧬 checking inference dependencies")
        download_inference_dependencies.remote(force=force_redownload)

        # Define fasta file
        if not fasta_file:
            fasta_file = here / "inputs" / "chai1_default_input.fasta"   
        print(f"🧬 running Chai inference on {fasta_file}")
        fasta_file = here / "inputs" / fasta_file
        print(fasta_file)
        fasta_content = Path(fasta_file).read_text()

        # Define inference config file
        if not inference_config_file:
            inference_config_file = here / "inputs" / "chai1_quick_inference.json"
        inference_config_file = here / "inputs" / inference_config_file
        print(f"🧬 loading Chai inference config from {inference_config_file}")
        inference_config = json.loads(Path(inference_config_file).read_text())

        # Generate a unique run ID
        run_id = hashlib.sha256(uuid4().bytes).hexdigest()[:8]  # short id
        print(f"🧬 running inference with {run_id=}")

        results = chai1_inference.remote(fasta_content, inference_config, run_id)

        # Define output directory
        output_dir = Path("./results")
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"🧬 saving results to disk locally in {output_dir}")
        for ii, (scores, cif) in enumerate(results):
            (Path(output_dir) / f"{run_id}-scores.model_idx_{ii}.npz").write_bytes(scores)
            (Path(output_dir) / f"{run_id}-preds.model_idx_{ii}.cif").write_text(cif)
        
        best_model, max_aggregate_score = select_best_model(
            run_id=run_id,
            scores_to_print=["aggregate_score", "ptm", "iptm"],
            number_of_scores=len(results),
            results_dir=str(output_dir)
        )
        # Take the last cif file and convert it to pdb
        cif_name = str(output_dir)+"/"+str(run_id)+"-preds.model_idx_"+str(best_model)+".cif"
        pdb_name = cif_name.split('.cif')[0] + '.pdb'
        st = gemmi.read_structure(cif_name)
        st.write_minimal_pdb(pdb_name)
        
        return pdb_name


# Create the Gradio interface
reps = [{"model": 0,"style": "cartoon","color": "hydrophobicity"}]

with gr.Blocks(theme=theme) as demo:
    
    gr.Markdown(
    """
    # Protein Folding Simulation Interface
    This interface provides you the tools to fold any FASTA chain based on Chai-1 model. Also, this is a MCP server to provide all the tools to automate the process of folding proteins with LLMs.     
    """) 
    
    with gr.Tab("Introduction 🔭"):
        
        gr.Image("images/logo1.png", show_label=False,width=400)
        
        gr.Markdown(
        """
        
        # Stakes 
        
        The industry is being deeply changed by the development of LLMs and the recent possibilities to provide them access to external tools. 
        For years now companies are using simulation tools in order faster and reduce the development cost of a product. 
        One of the challenge in the coming years will be to create agents that can setup, run and process simulations to faster the development of new products.
        
        # Objective 
        
        This project is a first step in this creating AI agents that perform simulations on existing softwares. 
        1) Several domains are of major interest: 
        - CFD (Computational Fluid Dynamics) simulations
        - Biology simulations (Protein Folding, Molecular Dynamics, etc.)
        - All applications that use neural networks
        
        --> This project is focused on the protein folding domain, but the same principles can be applied to other domains.
        
        2) Generally, industrial computations are performed on HPC clusters, which have access to large ressources. 
        
        --> The simulation need to run on a separate server
        
        3) The LLM needs to be able to access the simulation results in order to provide a complete answer to the user.
        
        --> The simulation results need to be accessible by the LLM
        
        ## Modal
        
        Modal (https://modal.com/) is a serverless platform that provides a simple way to run any application with the latest CPU and GPU hardware.
    
        ## Chai-1 Model
        
        Chai-1 (https://www.chaidiscovery.com/blog/introducing-chai-1) is a multi-modal foundation model for molecular structure prediction that performs at the state-of-the-art across a variety of benchmarks. 
        Chai-1 enables unified prediction of proteins, small molecules, DNA, RNA, glycosylations, and more.
        Chai-1 use on Modal server is an example on how to run folding simulations. 
        Thus, it is a good choice to start with. 
        
        # Work performed
        This interface allows you to run Chai1 simulations on a given Fasta sequence file.
        The Chai1 model is designed to predict the 3D structure of proteins based on their amino acid sequences.
        You can input a Fasta file containing the sequence of the molecule you want to simulate, and the output will be a 3D representation of the molecule based on the Chai1 model.

        You can input a Fasta file containing the sequence of the molecule you want to simulate.
        The output will be a 3D representation of the molecule based on the Chai1 model.
        
        ## Instructions
        1. Upload a Fasta sequence file containing the molecule sequence.
        2. Click the "Run" button to start the simulation.
        3. The output will be a 3D visualization of the molecule.
        
        # Disclaimer
        This interface is for educational and research purposes only. The results may vary based on the input sequence and the Chai1 model's capabilities.
        # Contact
        For any issues or questions, please contact the developer or refer to the documentation.   
        """) 
    
    with gr.Tab("Configuration 📦"):
        
        with gr.Row():
            with gr.Column(scale=1):
                slider_nb = gr.Slider(1, 500, value=200, label="Number of diffusion time steps", info="Choose the number of diffusion time steps for the simulation", step=1, interactive=True, elem_id="num_iterations")
                slider_trunk = gr.Slider(1, 5, value=3, label="Number of trunk recycles", info="Choose the number of iterations for the simulation", step=1, interactive=True, elem_id="trunk_number")
                slider_seed = gr.Slider(1, 100, value=42, label="Seed", info="Choose the seed", step=1, interactive=True, elem_id="seed")
                check_options = gr.CheckboxGroup(["ESM_embeddings", "MSA_server"], value=["ESM_embeddings",], label="Additionnal options", info="Options to use ESM embeddings and MSA server", elem_id="options")
                json_output = gr.Textbox(placeholder="Config file name", label="Config file name")
                button_json = gr.Button("Create Config file")
                button_json.click(fn=create_json_config, inputs=[slider_nb, slider_trunk, slider_seed, check_options], outputs=[json_output])
                
            with gr.Column(scale=1):   
                text_input = gr.Textbox(placeholder="Fasta format sequences", label="Fasta content", lines=10)
                text_output = gr.Textbox(placeholder="Fasta file name", label="Fasta file name")
                text_button = gr.Button("Create Fasta file")
                text_button.click(fn=create_fasta_file, inputs=[text_input], outputs=[text_output])
                
                gr.Markdown(
                """
                ## Example Fasta File
                ```
                >protein|name=example-protein
                AGSHSMRYFSTSVSRPGRGEPRFIAVGYVDDTQFVRFD      
                ```
                """)
        
       
    with gr.Tab("Run folding simulation 🚀"): 
        inp1 = gr.Textbox(placeholder="Fasta Sequence file", label="Input Fasta file")
        inp2 = gr.Textbox(placeholder="Config file", label="JSON Config file")
        btn = gr.Button("Run")
        out = Molecule3D(label="Molecule3D", reps=reps)
        btn.click(fn=compute_Chai1, inputs=[inp1 , inp2], outputs=[out])

# Launch both the Gradio web interface and the MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=True)
