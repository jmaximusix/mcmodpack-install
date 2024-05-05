import json
import requests
from urllib.parse import unquote
import sys
import zipfile
import os
import subprocess
import shutil

zip_filename = sys.argv[1]
output_dir = sys.argv[2]
tempdir = f"{output_dir}_temp"

print(f"Extracting {zip_filename} to {tempdir}...")

with zipfile.ZipFile(zip_filename, "r") as zip_ref:
    zip_ref.extractall(tempdir)

os.chdir(tempdir)

with open(f"manifest.json") as f:
    manifest = json.load(f)

mc_version = manifest["minecraft"]["version"]
forge_version = manifest["minecraft"]["modLoaders"][0]["id"].split("forge-")[1]
print(f"Modpack: {manifest['author']} - {manifest['name']}")
print("Required Minecraft version:", mc_version)
print("Required Forge version:", forge_version)
forge_download = input("Download and execute respective Forge installer? (y/N): ")
if forge_download.lower() == "y":
    forge_filename = f"forge-{mc_version}-{forge_version}-installer.jar"
    forge_link = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{mc_version}-{forge_version}/{forge_filename}"
    print(f"Downloading Forge installer...")
    response = requests.get(forge_link, allow_redirects=True)
    with open(f"{forge_filename}", "wb") as f:
        f.write(response.content)
    print("Running Forge installer...")
    subprocess.run(["java", "-jar", f"{forge_filename}"], check=True)

MODS_DIR = "additional_mods_temp"
if not os.path.exists(MODS_DIR):
    os.makedirs(MODS_DIR)
done_count = max(0, len(os.listdir(MODS_DIR)) - 1) # -1 bc last one might be only partially complete
modlist = manifest["files"][done_count:]
total_mods = len(modlist)

print(f"Downloading {total_mods} additional mods...\nNote: If this fails you're likely being rate limited by CurseForge. In that case, just retry later.")
for i,mod in enumerate(modlist, 1):
    modId = mod["projectID"]
    fileId = mod["fileID"]
    link = f"https://www.curseforge.com/api/v1/mods/{modId}/files/{fileId}/download"
    response = requests.get(link, allow_redirects=True)
    filename = unquote(response.url.split("/")[-1])
    with open(f"{MODS_DIR}/{filename}", "wb") as f:
        f.write(response.content)
    print(f"({i}/{total_mods}) {filename}")
print("Finished downloading mods.")

print(f"Moving everything to destination folder...")
os.rename("overrides", output_dir)
shutil.move(output_dir, "..")
for file in os.listdir(MODS_DIR):
    shutil.move(f"{MODS_DIR}/{file}", f"../{output_dir}/mods")

print("Cleaning up...")
os.chdir("..")
shutil.rmtree(tempdir)

print(f"Done! Now create a new launcher profile and point it to the {output_dir} directory and start playing :)")