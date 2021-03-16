import pandas as pd
import os, sys
import json

# directory = "/afs/cern.ch/work/c/camendol/CalibIOVs/"
directory = "/afs/cern.ch/work/c/camendol/LaserIOVs_new/2018/" + sys.argv[1] + "/"

filelistb = []
filelistg = []
filelist = []

beginb = []
beging = []
begin = []

iovb = []
iovg = []
iov = []

ib = 0
ig = 0
i = 0

for filename in os.listdir(directory):
    if filename.endswith(".txt") and len(filename.split("_")) < 3:
        print(int(os.popen("wc -l " + directory + filename).read().split()[0]))
        if int(os.popen("wc -l " + directory + filename).read().split()[0]) > 35000:
            print(directory + filename)
            if "IOVb" in filename:
                filelistb.append(directory + filename)
                beginb.append(filename.split("_")[1].replace(".txt", "").lstrip("0"))
                iovb.append(filename.split("_")[0] + str(ib))
                ib += 1
            if "IOVg" in filename:
                filelistg.append(directory + filename)
                beging.append(filename.split("_")[1].replace(".txt", "").lstrip("0"))
                iovg.append(filename.split("_")[0] + str(ig))
                ig += 1
            filelist.append(directory + filename)
            begin.append(filename.split("_")[1].replace(".txt", "").lstrip("0"))
            iov.append(filename.split("_")[0] + str(i))
            i += 1


df = pd.DataFrame({"file": filelist, "begin": begin, "iov": iov})
df["begin"] = df["begin"].astype("int")
df = df.reset_index().set_index("iov").drop(columns=["index"])
df = df[~df.index.duplicated(keep="first")]
print(df)

result = df.to_json(orient="index")

parsed = json.loads(result)
full = {}
full["IOVs"] = parsed
print(json.dumps(full, indent=4))

with open(directory + "ic-config.json", "w") as outfile:
    outfile.write(json.dumps(full, indent=4))

print("saved to " + directory + "ic-config.json")

df = pd.DataFrame({"file": filelistb, "begin": beginb, "iov": iovb})
df["begin"] = df["begin"].astype("int")
df = df.reset_index().set_index("iov").drop(columns=["index"])
df = df[~df.index.duplicated(keep="first")]
print(df)

result = df.to_json(orient="index")

parsed = json.loads(result)
full = {}
full["IOVs"] = parsed
print(json.dumps(full, indent=4))

with open(directory + "ic-configb.json", "w") as outfile:
    outfile.write(json.dumps(full, indent=4))

print("saved to " + directory + "ic-configb.json")

df = pd.DataFrame({"file": filelistg, "begin": beging, "iov": iovg})
df["begin"] = df["begin"].astype("int")
df = df.reset_index().set_index("iov").drop(columns=["index"])
df = df[~df.index.duplicated(keep="first")]
print(df)

result = df.to_json(orient="index")

parsed = json.loads(result)
full = {}
full["IOVs"] = parsed
print(json.dumps(full, indent=4))

with open(directory + "ic-configg.json", "w") as outfile:
    outfile.write(json.dumps(full, indent=4))

print("saved to " + directory + "ic-configg.json")
