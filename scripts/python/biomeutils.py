import json, os

###########################################
#Define Biome Names
#Master list of biome names to draw from
###########################################


class Biome:
    def __init__(self, name, aridity_index):
        self.name = name
        self.aridity_index = aridity_index



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


def writeJson(data, file_path):
    out_file = open(file_path, "w")
    json.dump(data, out_file, indent = 4, default = lambda d: d.__dict__)    #Serializes as JSON file format
    out_file.close()

def readJson(file_path):
    f = open(file_path)
    data = json.load(f)
    f.close()
    return data


def defaultBiomeSettings(file_path):
    biomes = { "biomes" : [Biome("Tropical Evergreen Forest", 2), Biome("Tropical Seasonal Forest", 8), Biome("Savannah", 4), Biome("Shrubland", 3), 
                Biome("Semi-desert", 1), Biome("Desert", 6), Biome("Prairie and Steppe", 4), Biome("Temperate Forest", 3), 
                Biome("Mixed Temperate Forest", 8), Biome("Boreal Evergreen Forest", 5), Biome("Boreal Seasonal Forest", 2),  
                Biome("Tundra", 8), Biome("Ice", 5), Biome("None", 2)]}

    # Create directory if it doesn't exist already
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    writeJson(biomes, file_path)




def readSettingsFile(file_path, hou_pwd):

    if not os.path.exists(file_path):
        defaultBiomeSettings(file_path)

    biome_settings_data = readJson(file_path)
    biomes = []

    hou_pwd.parm("fd_settings").set(len(biome_settings_data['biomes']))
    count = 1;

    for biome in biome_settings_data['biomes']:
        biome_attributes = Biome(biome['name'], biome['aridity_index'])
        hou_pwd.parm("biomename" + str(count)).set(biome_attributes.name)
        hou_pwd.parm("aridityindex" + str(count)).set(biome_attributes.aridity_index)
        count += 1

def saveSettingsFile(file_path, hou_pwd):
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

def saveFileLocation(file_location, profile_name):
    new_file_path = file_location + '/biome_settings_location.json'
    save_file_path = file_location + '/' + profile_name
    writeJson(save_file_path, new_file_path)

