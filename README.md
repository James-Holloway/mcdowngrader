# Minecraft World Downgrader 
A python script to downgrade your 1.15 worlds to 1.14. I created the script to downgrade a server build, meaning I could show it off using ReplayMod and shaders with OptiFine (both not avaliable for 1.15 at the time of writing)

Despite the fact that there should be no issues, please backup your world before doing this just in case. 

Due to the way 1.15 implements a larger array for biomes to allow for biomes to differ based on height, 1.14 fails to load the chunks. Minecraft then regenerates the chunk from scratch, meaning any work you have done in that chunk is lost. To avoid this, the whole biome tag is removed when the script is run, but will be regenerated fully when you reload the world. 

### Dependencies

- Python 3.8 (have not tested with older versions)
- [PySimpleGUI](https://github.com/PySimpleGUI/PySimpleGUI)
- [nbt](https://github.com/twoolie/NBT)

### How to use

- Run the script with python 3.8 with the above dependencies installed. This will open a simple GUI
- Worlds found in the folder will be displayed as their directory names
- If you have a custom location for your save, use "Browse" to select the folder that your world is located in
- Select your world from the list and back it up just in case (not avaliable through the script and hopefully shouldn't be needed)
- Press the Downgrade to "1.14.4" button, read the prompts and at the end, your 
- If you have any issues, please report them on the GitHub issues page

### Known issues

- Points of interest (villager workstations) are removed and will need to be reregistered when you load the chunks in
- Custom biomes are not saved. The biomes tags are removed and will need to be regenerated as their defaults when you load the world in Minecraft. The biomes are based on the world's generator. This should only be a minor issue

With some edits this script _may_ work with 1.13 or versions after 1.15 too, however I have not tested this. 
