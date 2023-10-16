from fastapi import FastAPI

import numpy as np
import pandas as pd
import requests
import json
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

import sys

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "https://apedul-client.vercel.app",
    "https://apedul.vercel.app",

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



load_dotenv()

app.nft_obj=pd.read_csv('csv-boredape.csv')  
app.last_token = 0
app.alchemy_api = os.getenv("ALCHEMY_API")

class Guess(BaseModel):
    question: list | None = []
    answer: list | None = []

class Answer(BaseModel):
    tokenId: list | None = []
    name: list| None = []
    description: list | None = []
    img: list | None = []
    question: list 
    answer: list 
    state: str 


def find_one(df, used_col):
  col = ""
  target = float('inf')
  for i in df.columns.tolist():
    if i == "tokenId" or i == "img" or i=='name':
      continue
    try:
      if abs(df[i].value_counts()[0]- (len(df)/2)) < target and i not in used_col:
        target = abs(df[i].value_counts()[0]- (len(df)/2))
        col = i
    except:
      if abs(df[i].value_counts()[1]- (len(df)/2)) < target and i not in used_col:
        target = abs(df[i].value_counts()[1]- (len(df)/2))
        col = i
  return col

def find_two(df, used_col=[], ans=[]):
    for i in range(len(used_col)):
        df = df[df[used_col[i]] == ans[i]]
    if len(df) <= 1:
        return df, used_col, ans, True

    col = find_one(df,used_col)
    if col == "":
        return df, used_col, ans, True

    used_col.append(col)
    return df, used_col, ans, False


@app.get("/")
async def root():
    return "Welcome to api of apedul | akinator inspired for web3 NFTs"
      
# @app.get("/setup")
# async def setup():
    url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{app.alchemy_api}/getNFTsForCollection?collectionSlug=boredapeyachtclub&withMetadata=true&startToken={app.last_token}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)

    obj = json.loads(response.text)
    objs = []
    for i in obj["nfts"]:
        finalobj = {}
        finalobj['tokenId'] = i['id']['tokenId']
        finalobj['attributes'] = {}
        for trait in i['metadata']['attributes']:
            finalobj['attributes'][trait['trait_type']] = trait['value']
        finalobj['img'] = i['media'][0]['gateway']
        finalobj['name'] = i['title']
        objs.append(finalobj)

    nft_obj = {}
    nft_obj['tokenId'] = []
    nft_obj['img'] = []
    nft_obj['name'] = []
    for i in objs:
        nft_obj['tokenId'].append(i['tokenId'])
        nft_obj['img'].append(i['img'])
        nft_obj['name'].append(i['name'])

        for key in i['attributes']:
            if key in nft_obj:
                for m in range(len(nft_obj['tokenId'])-len(nft_obj[key]) -1):
                    nft_obj[key].append(0)
                nft_obj[key].append(1)
            else:
                nft_obj[key] = []
                for nt in range(len(nft_obj['tokenId'])-1):
                    nft_obj[key].append(0)
                nft_obj[key].append(1)
            
            if key+"_"+i['attributes'][key] in nft_obj:
                for m in range(len(nft_obj['tokenId'])-len(nft_obj[key+"_"+i['attributes'][key]]) -1):
                    nft_obj[key+"_"+i['attributes'][key]].append(0)
                nft_obj[key+"_"+i['attributes'][key]].append(1)
            else:
                nft_obj[key+"_"+i['attributes'][key]] = []
                for nt in range(len(nft_obj['tokenId'])-1):
                    nft_obj[key+"_"+i['attributes'][key]].append(0)
                nft_obj[key+"_"+i['attributes'][key]].append(1)

    for key in nft_obj:
        for i in range(len(nft_obj['tokenId']) - len(nft_obj[key])):
            nft_obj[key].append(0)

    #save last token
    app.last_token += len(nft_obj["tokenId"])
    print(nft_obj["tokenId"][-1])

    if app.nft_obj == {}:
        app.nft_obj = nft_obj
    else:
        res = pd.merge( pd.DataFrame(data=app.nft_obj), pd.DataFrame(data=nft_obj), how="outer")
        res = res.fillna(0)
        app.nft_obj = res.to_dict('list')

    return nft_obj

# @app.
@app.post("/guess")
async def guess(item: Guess):
    df, used_col, ans, state = find_two(app.nft_obj,item.question, item.answer)
    if state:
        result = Answer(state = "Done", question=used_col, answer=ans)
        result.name = df.name.values.tolist()
        result.img = df.img.values.tolist()
        result.tokenId = df.tokenId.values.tolist()
    else:
        result = Answer(state = "Pending", question=used_col, answer=ans)

    return result

print(sys.getsizeof(app.nft_obj))