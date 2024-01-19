import json, os

###########################################
#Define Biome Names
#Master list of biome names to draw from
###########################################


#Useful function to write a JSON-formatted string out to file
def writeJson(data, file_path):
    out_file = open(file_path, "w")
    json.dump(data, out_file, indent = 4, default = lambda d: d.__dict__)    #Serializes as JSON file format
    out_file.close()

#Useful function to read a JSON-formatted file
def readJson(file_path):
    f = open(file_path)
    data = json.load(f)
    f.close()
    return data


#Class definition to store biome attributes and later add more
class Biome:
    def __init__(self, name, aridity_index):
        self.name = name
        self.aridity_index = aridity_index


#Used by HDAS to read biome profiles and populate dropdown menus with a list of biomes
#Used by Biome Curve Setup and Biome Initialize in the Biome Name parameters under Menu -> Menu Script
def biomeNames(biome_json):
    
    biomes = []
    biome_list = readJson(biome_json)['biomes']
    
    for biome in biome_list:
        biomes.append(biome['name'])
    

    biome_extension = []
    
    for b in biomes:
        #Menu items need twice the number of entries
        biome_extension.append(b)
        biome_extension.append(b)
        
    return biome_extension


#Sets the default biome settings for newly created files. Will need to be updated with addition of new attributes
#Used by the readSettingsFile function
def defaultBiomeSettings(file_path):
    biomes = { "biomes" : [Biome("Tropical Evergreen Forest", 2), Biome("Tropical Seasonal Forest", 8), Biome("Savannah", 4), Biome("Shrubland", 3), 
                Biome("Semi-desert", 1), Biome("Desert", 6), Biome("Prairie and Steppe", 4), Biome("Temperate Forest", 3), 
                Biome("Mixed Temperate Forest", 8), Biome("Boreal Evergreen Forest", 5), Biome("Boreal Seasonal Forest", 2),  
                Biome("Tundra", 8), Biome("Ice", 5), Biome("None", 2)]}

    # Create directory if it doesn't exist already
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    writeJson(biomes, file_path)


#Reads the biome profile JSON and populates HDA multiparm with stored attribute values
#Used by Biome Profile. Under Scripts ->PythonModule/OnCreated. 
#In the PythonModule, used for the loadProfile function there. This is accessed in a callback script by multiple HDA parameters
def readSettingsFile(file_path, hou_pwd):

    if not os.path.exists(file_path):
        defaultBiomeSettings(file_path)

    biome_settings_data = readJson(file_path)
    biomes = []

    #Next few lines set the multiparm settings on the corresponding Biome Profile HDA. These parameter reference names are hard-coded
    #Parameters should be added here as more are added to the HDA
    hou_pwd.parm("fd_settings").set(len(biome_settings_data['biomes']))
    count = 1;

    for biome in biome_settings_data['biomes']:
        biome_attributes = Biome(biome['name'], biome['aridity_index'])
        hou_pwd.parm("biomename" + str(count)).set(biome_attributes.name)
        hou_pwd.parm("aridityindex" + str(count)).set(biome_attributes.aridity_index)
        count += 1


#Saves the parameters set on the HDA interface as a biome profile JSON
#Used by Biome Profile. Under Scripts ->PythonModule
#Used for the saveProfile function there. This is accessed in a callback script on the Save Profile parameter
def saveSettingsFile(file_path, hou_pwd):

    #Next few lines get the multiparm settings on the corresponding Biome Profile HDA. These parameter reference names are hard-coded
    #Parameters should be added here as more are added to the HDA
    biome_num =  hou_pwd.parm("fd_settings").eval()
    biome_list = []
    
    for i in range(biome_num):
        i += 1
        biome_eval = Biome("", 0)

        biome_eval.name = hou_pwd.parm("biomename" + str(i)).eval()
        biome_eval.aridity_index = hou_pwd.parm("aridityindex" + str(i)).eval()
        biome_list.append(biome_eval)

    biomes = { "biomes" : biome_list} 

    # Create directory if it doesn't exist already
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    writeJson(biomes, file_path)

