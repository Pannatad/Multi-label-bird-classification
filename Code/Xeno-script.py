import requests
import os
import pandas as pd
from tqdm import tqdm
from pydub import AudioSegment

# --- Config ---
species_list = [
    "centropus sinensis",
    "coracias affinis",
    "geopelia striata",
    "amaurornis phoenicurus",
    "lonchura punctulata",
    "streptopelia tranquebarica",
    "spilopelia chinensis",
    "treron vernans",
    "cacomantis merulinus",
    "anastomus oscitans",
    "microcarbo niger",
    "ixobrychus sinensis",
    "ixobrychus cinnamomeus",
    "ardeola bacchus",
    "ardeola speciosa",
    "butorides striata",
    "athene brama",
    "pelargopsis capensis",
    "halcyon smyrnensis",
    "halcyon pileata",
    "merops philippinus",
    "psilopogon haemacephalus",
    "oriolus chinensis",
    "aegithina tiphia",
    "rhipidura javanica",
    "dicrurus leucophaeus",
    "corvus macrorhynchos",
    "prinia flaviventris",
    "prinia inornata",
    "pycnonotus goiavier",
    "pycnonotus conradi",
    "gracupica nigricollis",
    "gracupica contra",
    "acridotheres tristis",
    "acridotheres grandis",
    "copsychus saularis",
    "dicaeum cruentatum",
    "anthreptes malacensis"
]

max_per_species = 50
region = "thailand"
quality_set = {"A", "B"}
save_root = "xeno_audio"

metadata_rows = []

for species in species_list:
    query = f'{species} cnt:{region}'
    page = 1
    downloaded = 0
    species_folder = f"{save_root}/{species.replace(' ', '_')}"
    os.makedirs(species_folder, exist_ok=True)
    print(f"\n--- Downloading: {species} ---")

    while downloaded < max_per_species:
        url = f"https://xeno-canto.org/api/2/recordings?query={query}&page={page}"
        resp = requests.get(url)
        data = resp.json()
        if "recordings" not in data or not data["recordings"]:
            print(f"No more recordings found on page {page} for {species}.")
            break

        recs = data["recordings"]

        for rec in recs:
            if downloaded >= max_per_species:
                break
            if rec["q"] not in quality_set:
                continue

            # Compose local filenames
            base_name = f"{rec['id']}_{rec['en'].replace(' ', '_')}_{rec['cnt']}_{rec['q']}"
            mp3_fn = base_name + ".mp3"
            wav_fn = base_name + ".wav"
            mp3_path = os.path.join(species_folder, mp3_fn)
            wav_path = os.path.join(species_folder, wav_fn)
            audio_url = "https:" + rec["file"] if rec["file"].startswith("//") else rec["file"]

            # Download audio
            try:
                audio = requests.get(audio_url, timeout=10)
                with open(mp3_path, "wb") as f:
                    f.write(audio.content)

                # Convert mp3 to wav
                try:
                    sound = AudioSegment.from_mp3(mp3_path)
                    sound.export(wav_path, format="wav")
                    os.remove(mp3_path)  # Remove mp3 after conversion (optional)
                except Exception as convert_err:
                    print(f"Failed to convert {mp3_path} to wav: {convert_err}")
                    continue

                # Save metadata (use wav filename)
                metadata_rows.append({
                    "filename": wav_path,
                    "species": rec["en"],
                    "scientific_name": rec["gen"] + " " + rec["sp"],
                    "location": rec["loc"],
                    "country": rec["cnt"],
                    "length": rec["length"],
                    "quality": rec["q"],
                    "date": rec["date"],
                    "id": rec["id"],
                    "url": f"https://xeno-canto.org/{rec['id']}"
                })
                downloaded += 1
                print(f"Downloaded {downloaded}/{max_per_species} for {species}: {wav_fn}")
            except Exception as e:
                print(f"Failed to download or convert: {audio_url} ({e})")
        page += 1

# Save metadata
df = pd.DataFrame(metadata_rows)
df.to_csv(os.path.join(save_root, "metadata.csv"), index=False)
print("\nAll done. Metadata written to metadata.csv")
