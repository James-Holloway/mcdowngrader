#!python3.8

import os, sys, nbt
import platform as plat
import PySimpleGUI as sg

#Doesn't need to be changed unless you have a custom MC install directory
platform = plat.system() 
if platform == "Windows":
    saveFolder = os.path.expandvars("%appdata%\\.minecraft\\saves\\")
elif platform == "Linux":
    saveFolder = "~/.minecraft/saves"
elif platform == "Darwin":
    saveFolder = "~/Library/Application Support/minecraft/saves"
else:
    print(f"Unexpected platform - {platform}")
    saveFolder = ""
#Use this to change what you want to change the world version to. Only works with 1.14 at the moment
#
setWorldVer = "1.14"
#Will slow down the execution of the program to show pointless information
debug = False

#This code does not make every version magically work, only changes the version id and the things that crash 1.15 worlds in 1.14 (mainly biomes)
#Add other versions from https://minecraft.gamepedia.com/Data_version
#1.15 worlds to 1.14 - min to max
dataversions = {"1.15":{"19w36a":2203, "1.15.2":2230}, "1.14":{"1.14":1952, "1.14.4":1976}}

#Loads in the necessary variables for converting
#Extra is used for DIM1 and DIM-1
def init(extra=""):
    global leveldat, level, world
    
    #Path to the level.dat
    if extra == "": leveldat = saveFolder + "/" + saveName + extra + "/level.dat" #If dimension is specified then we don't want to look for the level.dat

    #Loading in the NBT related stuff
    level = nbt.nbt.NBTFile(leveldat)
    world = nbt.world.WorldFolder(saveFolder + "/" + saveName + extra)
    

#Gets the world version from the level.dat
def getWorldVersion():
    name = level.tags[0].get("Version").get("Name").value
    ID = level.tags[0].get("Version").get("Id").value
    ID2 = level.tags[0].get("DataVersion").value
    return name, ID, ID2

#Sets the world version to the level.dat
def setWorldVersion(versionName, versionId):
    level.tags[0]["Version"]["Name"] = nbt.nbt.TAG_String(name="Name", value=versionName)
    level.tags[0]["Version"]["Id"] = nbt.nbt.TAG_Int(name="Id", value=versionId)
    level.tags[0]["DataVersion"] = nbt.nbt.TAG_Int(name="DataVersion", value=versionId)
    level.write_file(leveldat)

if debug:
    #Return the first chunk, for debug purposes
    def getChunk():
        for chunk in world.iter_nbt():
            return chunk
    #Returns the first region, for debug purposes
    def getRegion():
        for region in world.iter_regions():
            return region

#Gets the first chunk's DataVersion, used in print statements
def getChunkVersion():
    for chunk in world.iter_nbt():
        return chunk["DataVersion"].value
        break

#Sets all the chunks to the passed dataversion
#Also removes the chunk biomes (for now) to get around the 1024 int vs 256 int array differences
def setChunkVersion(dataver):
    if debug: print("Data version before", getChunkVersion())
    errors = 0
    total = 0
    for region in world.iter_regions(): #can't use the world.iter_nbt due to not being able to write
        regX = region.loc.x #region x and z locations
        regZ = region.loc.z

        for meta in region.get_metadata(): #get the chunk location from the meta. Otherwise, we can't write to the region with
            total += 1
            chunk = removeChunkBiomes(region.get_chunk(meta.x, meta.z)) #Passes the chunk with the biomes already stripped out
            
            if dataver == chunk["DataVersion"].value:
                if debug: print(f"Skipped chunk {meta.x},{meta.z} - dataversion is the same - {dataver},{chunk['DataVersion'].value}")
                continue
            try:
                chunk["DataVersion"] = nbt.nbt.TAG_Int(name="DataVersion", value=dataver)
                region.write_chunk(meta.x, meta.z, chunk) #Writes the chunk into the region, probably a bit inefficient to write multiple times per region, but this is easier
                if debug: print("Successful conversion", meta.x, meta.z, region.loc, chunk["DataVersion"].value)
            except KeyError:
                errors += 1
                print(f"Unsuccessful conversion - {meta.x},{meta.z} in region {region.loc}")
    
    if debug: print(f"Errors: {errors}/{total}")
    if debug: print("Data version after", getChunkVersion())

#Removes the biomes from the passed chunk
#1.15 uses 1024 length int arrays so each 4 vertical blocks can have a different biome
#1.14 uses 256 length int array. This issue makes the chunk unloadable in previous versions
def removeChunkBiomes(chunk):
    if chunk["Level"].get("Biomes"):
        chunk["Level"].pop("Biomes")
    return chunk

#Removes the point of interest folder because it is harder to parse non-gzip'd files
#Fails the loading of chhunks due these .mca files also having 1024 length biomes
#By removing it, we erase all the villager memories
#However, these should be regenerated at runtime
def removePOIFolder():
    return os.rename(world.worldfolder + "/poi", world.worldfolder +"/poi-disabled")

#Doesn't work yet and isn't needed
def setPlayerDataVersion(dataver):
    for root, dirs, files in os.walk(world.worldfolder+"playerdata"):
        print(files)
        #nbt.nbt.NBTFile()
        #not functioning yet

#Scans for 1.15 worlds in the saves folder
def scanWorlds():
    global dataversions, saveFolder
    
    allWorlds = os.listdir(os.path.expandvars(saveFolder))
    goodWorlds = []
    for world in allWorlds:
        try:
            level = nbt.nbt.NBTFile(saveFolder + "/" + world + "/level.dat") #Could throw FileNotFoundError
        
            worldDataVer = level.tags[0].get("Version").get("Id").value #Could throw KeyError and AttributeError
            minMaxVers = list(dataversions["1.15"].values())
            if worldDataVer in range(minMaxVers[0], minMaxVers[-1]+1): #If is a 1.15 world (well, since the new biome structure)
                goodWorlds.append(world)
        except KeyError:
            pass
        except NameError: #if a variable isn't declared, we'll get this bad boy
            pass
        except AttributeError:
            pass
        except FileNotFoundError: #We expect many of these, especially if the save folder is not valid
            pass
    if debug: print(f"Appropriate folders: {len(goodWorlds)}/{len(allWorlds)}")
    return goodWorlds

#Converts any world from the 1.15 era (and possibly above) to 1.14 (and possibly 1.13)
def convert():
    if debug: print(f"World version is {getWorldVersion()[0]}")

    dataver = list(dataversions[setWorldVer].values())[-1] #Gets the highest data version from that dataversion
    if debug: print(f"{saveName} was {getWorldVersion()}")

    setWorldVersion(setWorldVer, dataver) #level.dat
    setChunkVersion(dataver) #region files
    
    if debug: print(f"{saveName} is now {getWorldVersion()}")
    if debug: print("Removing POI folder")
    removePOIFolder() #Removes the POI folder, see reason above function defenition
    
    #Other dimensions now
    try: #NETHER Dimension
        if debug: print("Converting Nether")
        init("/DIM-1/")
        setChunkVersion(dataver)
        removePOIFolder()
    except FileNotFoundError as e:
        if debug: print(f"Failed to convert The Nether, file not found - {e}")
    
    try: #END Dimension
        if debug: print("Converting End")
        init("/DIM1/")
        setChunkVersion(dataver)
        removePOIFolder()
    except FileNotFoundError as e:
        if debug: print(f"Failed to convert The End, file not found - {e}")
    
    if debug: print(f"{saveName} should be converted now")

#Shows an error on the window
def windowError(errorText):
    global window
    window["errors"].update(errorText)
    window.Refresh()

#Scans the folder
def scanFolder():
    window["worlds"].update([])
    if values.get("savesFolderInput"):
        potentialFolder = values.get("savesFolderInput")
        if potentialFolder[-1] != "\\" and potentialFolder[-1] != "/": #So that if the \\ or / has not been appended, we add it
            potentialFolder += "/"
        if os.path.isdir(potentialFolder) and os.path.exists(potentialFolder):
            saveFolder = potentialFolder
            worlds = scanWorlds()
            if len(worlds) > 0:
                window["worlds"].update(values=worlds) #Updates the world listbox
            else:
                windowError("Could not find any 1.15 saves")
                if debug: print(f"Could not find 1.15 saves - {worlds}")
        else:
            windowError("Input folder does not exist")
            if debug: print(f"Input folder does not exist - {potentialFolder}")
        
#Do the GUI
if __name__ == "__main__":
    worlds = scanWorlds()
    if len(worlds) == 0:
        if debug: print("Error: No worlds found in the default directory")

    sg.theme("SystemDefault1")

    layout = [ [sg.Text("Saves folder", justification="center", pad=(0,0)),
                sg.Input(saveFolder,(66,1), disabled=True, text_color=sg.rgb(95,95,95), key="savesFolderInput", enable_events=True, tooltip="The folder that contains your saves"), #Disabled input for current file purposes
                sg.FolderBrowse(initial_folder=saveFolder, key="folderBrowse")], #Saves folder, autotargets previous element
                [ sg.Listbox(worlds, size=(64,6), key="worlds"), sg.Submit("Downgrade to 1.14.4", key="submit", tooltip="This removes point of interests and biomes\nThey are regenerated when you load the world in Minecraft\nBackup your world before doing this") ], #Listbox
                [sg.Text("Errors:",pad=(0,0)), sg.Text(" "*72, text_color=sg.rgb(255,24,24), key="errors")] #Errors
              ]
    window = sg.Window("Minecraft World Downgrader - 1.15 to 1.14", default_element_size=(40,1), size=(None,None), margins=(2,2)).Layout(layout) #Creating the window
    
    while True:
        event, values = window.Read()
        windowError("")
        if debug: print(f"Window event is {event}")
        if event == "submit":
            if values.get("worlds"):
                saveName = values["worlds"][0]
                sg.Popup(f"Starting Conversion of "+saveName, "This GUI will not respond but will be doing things in the background", "Please don't close it mid-process", title="Starting Conversion", button_type=sg.POPUP_BUTTONS_OK)
                init()
                if debug: print(f"Converting {saveName} to 1.14.4\nFolder: {saveFolder}")
                convert()
                sg.Popup(f"Conversion of {saveName} to 1.14.4 is complete.", "Thank you for using this tool", title="Conversion Complete", button_type=sg.POPUP_BUTTONS_OK)
                scanFolder()
                #window.Close()
            else: #world has not yet been selected
                windowError("No world selected")

        elif event == "savesFolderInput":
            if values.get("savesFolderInput"):
                if debug: print(f"Folder set to - {values['savesFolderInput']}")
                savesFolderInput = values.get("savesFolderInput")
                if savesFolderInput and os.path.exists(savesFolderInput) and os.path.isdir(savesFolderInput):
                    window["folderBrowse"].InitialFolder = savesFolderInput
                    saveFolder = savesFolderInput
                    scanFolder()
                else:
                    windowError("Saves folder input is not valid")
                    if debug: print(f"Saves folder input is not valid - {savesFolderInput}")
            else:
                if debug: print(f"Could not get folderBrowse - {values}")
        elif event == None:
            if debug: print("Closing window")
            break
    
    if "idlelib" not in sys.modules:
        input("\nPress enter to exit...")
