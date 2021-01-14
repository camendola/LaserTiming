import pandas as pd
import os



directory= "/afs/cern.ch/work/c/camendol/LaserIOVs/2018/B/"

for filename in os.listdir(directory):
    
    if len(filename.split("_"))<3 :
        temp_path = os.path.join(directory, 'temp.txt')
        with open(directory+filename, 'r') as f_read, open(temp_path, 'w') as temp:
            for line in f_read:
                line = line.replace("  ", " ")
                if len(line.split (" ") )< 5 :
                    continue
                temp.write(line)
            print(temp)

        os.rename(temp_path, directory+filename.replace(".txt", "_fix.txt"))
        print (filename)
   
    else:
        continue
