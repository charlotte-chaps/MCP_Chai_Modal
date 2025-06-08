# Import libraries
from pathlib import Path
import modal

# Define parameters for the Modal app
here = Path(__file__).parent  # the directory of this file

MINUTES = 60  # seconds

image = modal.Image.debian_slim(python_version="3.12").run_commands(
    "uv pip install --system --compile-bytecode torch>=2.6.0 chai_lab==0.6.1 hf_transfer==0.1.8 "
)

chai_model_volume = (
    modal.Volume.from_name(  # create distributed filesystem for model weights
        "chai1-models",
        create_if_missing=True,
    )
)
models_dir = Path("/models/chai1")

image = image.env(  # update the environment variables in the image to...
    {
        "CHAI_DOWNLOADS_DIR": str(models_dir),  # point the chai code to it
        "HF_HUB_ENABLE_HF_TRANSFER": "1",  # speed up downloads
    }
)

chai_preds_volume = modal.Volume.from_name("chai1-preds", create_if_missing=True)
preds_dir = Path("/preds")

# Define the Modal app
app = modal.App("Chai1 inference")

@app.function(
    timeout=15 * MINUTES,
    gpu="H100",
    volumes={models_dir: chai_model_volume, preds_dir: chai_preds_volume},
    image=image,
)
def chai1_inference(
    fasta_content: str, inference_config: dict, run_id: str
) -> list[(bytes, str)]:
    from pathlib import Path

    import torch
    from chai_lab import chai1

    N_DIFFUSION_SAMPLES = 5  # hard-coded in chai-1

    fasta_file = Path("/tmp/inputs.fasta")
    fasta_file.write_text(fasta_content.strip())

    output_dir = Path("/preds") / run_id

    chai1.run_inference(
        fasta_file=fasta_file,
        output_dir=output_dir,
        device=torch.device("cuda"),
        **inference_config,
    )

    print(
        f"🧬 done, results written to /{output_dir.relative_to('/preds')} on remote volume"
    )

    results = []
    for ii in range(N_DIFFUSION_SAMPLES):
        scores = (output_dir / f"scores.model_idx_{ii}.npz").read_bytes()
        cif = (output_dir / f"pred.model_idx_{ii}.cif").read_text()

        results.append((scores, cif))

    return results

@app.function(volumes={models_dir: chai_model_volume})
async def download_inference_dependencies(force=False):
    import asyncio

    import aiohttp

    base_url = "https://chaiassets.com/chai1-inference-depencencies/"  # sic
    inference_dependencies = [
        "conformers_v1.apkl",
        "models_v2/trunk.pt",
        "models_v2/token_embedder.pt",
        "models_v2/feature_embedding.pt",
        "models_v2/diffusion_module.pt",
        "models_v2/confidence_head.pt",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    # launch downloads concurrently
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for dep in inference_dependencies:
            local_path = models_dir / dep
            if force or not local_path.exists():
                url = base_url + dep
                print(f"🧬 downloading {dep}")
                tasks.append(download_file(session, url, local_path))

        # run all of the downloads and await their completion
        await asyncio.gather(*tasks)

    chai_model_volume.commit()  # ensures models are visible on remote filesystem before exiting, otherwise takes a few seconds, racing with inference


async def download_file(session, url: str, local_path: Path):
    async with session.get(url) as response:
        response.raise_for_status()
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            while chunk := await response.content.read(8192):
                f.write(chunk)