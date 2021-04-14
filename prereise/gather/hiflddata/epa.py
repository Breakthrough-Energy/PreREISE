
import glob
import pandas as pd
import csv
import json
import os.path
from scipy import optimize
 
def marge(csv_list, outputfile):
    for inputfile in csv_list:
        f = open(inputfile, 'r', encoding="utf-8")
        data = pd.read_csv(f)
        data.to_csv(outputfile, mode='a', index=False)
 
def distinct(file):
    df = pd.read_csv(file, header=None)
    datalist = df.drop_duplicates()
    datalist.to_csv('result_new.csv', index=False, header=False)

def clean_epa():
    df = pd.read_csv('result.csv',usecols=['FACILITY_NAME','UNITID','OP_TIME','GLOAD (MW)','HEAT_INPUT (mmBtu)'])
    Num_sub = len(df)
    row_indexs = []
    for i in range(Num_sub):
    if(pd.isnull(df['OP_TIME'][i]) or (df['OP_TIME'][i] == 0.0) or pd.isnull(df['GLOAD (MW)'][i]) or (df['GLOAD (MW)'][i] == 0.0) or pd.isnull(df['HEAT_INPUT (mmBtu)'][i]) or (df['HEAT_INPUT (mmBtu)'][i] == 0.0)):
        row_indexs.append(i)
    clean_data = df.drop(labels = row_indexs)
    clean_data.to_csv('data/epa.csv',index=False, header=False)

def getGen():
    gen = []
    csv_data = pd.read_csv("data/General_Units.csv")
    df = np.array(csv_data)
    needs = df.tolist()
    for pla in needs:
        name = (pla[13],pla[2])
        if(name not in gen):
            gen.append(name)
    return gen

def getEpaDict(gen):
    epa = {}
    csv = pd.read_csv('epa.csv',header=None)
    df = np.array(csv)
    em = df.tolist()
    for pla in em:
        if(pla[2] == 'OP_TIME'):
            continue
        name = (str(pla[0]).upper(),pla[1])
        if(name not in gen):
            name = str(pla[0]).upper() + '-cc'
        if(name not in epa):
            hour = float(pla[2])
            if(hour != 0.0):
                heat = float(pla[4])/hour
                load = float(pla[3])
                epa[name] = [(load,heat)]
        else:
            hour = float(pla[2])
            if(hour != 0.0):
                heat = float(pla[4])/hour
                load = float(pla[3])
                epa[name].append((load,heat))
    return epa


def aggList(list1,list2):
    list3 = []
    len1 = len(list1)
    len2 = len(list2)
    if(len1 < len2):
        list1, list2 = list2, list1
    for i in range(len(list2)):
        tu1 = list1[i]
        tu2 = list2[i]
        tu3 = (tu1[0]+tu2[0],tu1[1]+tu2[1])
        list3.append(tu3)
    list3.extend(list1[len(list1)-len(list2):-1])
    
    return list3

def Clean_p(P_csv):
    csv_data = pd.read_csv(P_csv)
    Num_sub = len(csv_data)
    row_indexs = []
    for i in range(Num_sub):
        if(csv_data['STATUS'][i] != 'OP'):
            row_indexs.append(i)
    clean_data = csv_data.drop(labels = row_indexs)
    return clean_data

def Plant_agg(clean_data,epa):
    plant_dict = {}
    n = 0
    p=0
    q=0
    for index, row in clean_data.iterrows():
        tu = (row['PLANT'],row['PRIM_FUEL'],row['PRIM_MVR'])
        r = (row['PLANT'],row['NAME'])
        if(tu not in plant_dict):
            if(r in epa):
                p=p+1
                plant_dict[tu] = epa[r]
            elif((row['PLANT'] + '-cc') in epa):
                q=q+1
                plant_dict[tu] = epa[row['PLANT'] + '-cc']
            else:
                for key in epa:
                    if(isinstance(key,tuple)):
                        if(row['PLANT'] in key[0]):
                            plant_dict[tu] = epa[key]
                            break;
                    else:
                        if(row['PLANT'] in key):
                            plant_dict[tu] = epa[key]
                            break;

        else:
            if(r in epa):
                p = p+1
                list1 = plant_dict[tu]
                plant_dict[tu] = aggList(list1,epa[r])
            elif((row['PLANT'] + '-cc') in epa):
                q=q+1
                plant_dict[tu] = epa[row['PLANT'] + '-cc']
            else:
                for key in epa:
                    if(isinstance(key,tuple)):
                        if(row['PLANT'] in key[0]):
                            plant_dict[tu] = epa[key]
                            break;
                    else:
                        if(row['PLANT'] in key):
                            plant_dict[tu] = epa[key]
                            break;

    return plant_dict

def func(x,a,b,c):
    return a*x**2 + b*x + c

def to_csv(plant_dict):
    curve = open('data/curve.csv','w',newline='')
    csv_writer = csv.writer(curve)
    csv_writer.writerow(["plant_id","c2","c1","c0"])
    for key in plant_dict:
        x = []
        y = []
        for tup in plant_dict[key]:
            x.append(tup[0])
            y.append(tup[1])
        param_bounds=([0,-np.inf,-np.inf],[np.inf,np.inf,np.inf])
        popt, pcov=optimize.curve_fit(func,x,y,bounds=param_bounds)
        c2 = popt[0]
        c1 = popt[1]
        c0 = popt[2]
        csv_writer.writerow([key[0]+'-'+key[1]+'-'+key[2],c2,c1,c0])
    curve.close()

if __name__ == '__main__':
    #csv_list = glob.glob('D:/2018/*.csv')
    #output_csv_path = 'result.csv'
    #print(csv_list)
    #marge(csv_list, output_csv_path)
    #distinct(output_csv_path)
    gen = getGen()
    epa = getEpaDict(gen)
    clean_data = Clean_p("data/General_Units.csv")
    plant_dict = Plant_agg(clean_data,epa)
    to_csv(plant_dict)
