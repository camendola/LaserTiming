import pandas as pd
import os
import json

#directory = "/afs/cern.ch/work/c/camendol/CalibIOVs/"
directory = "/afs/cern.ch/work/c/camendol/LaserIOVs/2018/B/"
filelist = []
begin = []
iov = []
i = 0
for filename in os.listdir(directory):
    if filename.endswith(".txt") and len(filename.split("_")) < 3:
        print (int(os.popen('wc -l '+directory+filename).read().split(  )[0]))
        if int(os.popen('wc -l '+directory+filename).read().split(  )[0])> 50000:
            print (directory+filename)
            filelist.append(directory+filename)
            begin.append(filename.split("_")[1].replace(".txt","").lstrip("0"))
            iov.append(filename.split("_")[0]+str(i))
            i += 1

#print(filelist)

df = pd.DataFrame({"file":filelist, "begin":begin, "iov":iov})
df["begin"]= df["begin"].astype("int")
df = df.reset_index().set_index("iov").drop(columns = ["index"])
df = df[~df.index.duplicated(keep='first')]
print(df)

result = df.to_json(orient="index")
parsed = json.loads(result)
print(json.dumps(parsed, indent=4))


with open(directory+"ic-config.json", "w") as outfile: 
    outfile.write(json.dumps(parsed, indent=4)) 

print("saved to "+directory+"ic-config.json")
