from fastapi import FastAPI

import numpy as np
from scipy.stats import entropy
import pandas as pd
import requests
import json
from pydantic import BaseModel
import os
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

app.nft_obj={}
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
    return app.nft_obj
      
@app.get("/setup")
async def setup():
    print(app.alchemy_api)
    url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{app.alchemy_api}/getNFTsForCollection?collectionSlug=boredapeyachtclub&withMetadata=true"
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

    app.nft_obj = {}
    app.nft_obj['tokenId'] = []
    app.nft_obj['img'] = []
    app.nft_obj['name'] = []
    for i in objs:
        app.nft_obj['tokenId'].append(i['tokenId'])
        app.nft_obj['img'].append(i['img'])
        app.nft_obj['name'].append(i['name'])

        for key in i['attributes']:
            if key in app.nft_obj:
                for m in range(len(app.nft_obj['tokenId'])-len(app.nft_obj[key]) -1):
                    app.nft_obj[key].append(0)
                app.nft_obj[key].append(1)
            else:
                app.nft_obj[key] = []
                for nt in range(len(app.nft_obj['tokenId'])-1):
                    app.nft_obj[key].append(0)
                app.nft_obj[key].append(1)
            
            if key+"_"+i['attributes'][key] in app.nft_obj:
                for m in range(len(app.nft_obj['tokenId'])-len(app.nft_obj[key+"_"+i['attributes'][key]]) -1):
                    app.nft_obj[key+"_"+i['attributes'][key]].append(0)
                app.nft_obj[key+"_"+i['attributes'][key]].append(1)
            else:
                app.nft_obj[key+"_"+i['attributes'][key]] = []
                for nt in range(len(app.nft_obj['tokenId'])-1):
                    app.nft_obj[key+"_"+i['attributes'][key]].append(0)
                app.nft_obj[key+"_"+i['attributes'][key]].append(1)

    for key in app.nft_obj:
        for i in range(len(app.nft_obj['tokenId']) - len(app.nft_obj[key])):
            app.nft_obj[key].append(0)

    df = pd.DataFrame(data=app.nft_obj)

    return app.nft_obj

# @app.
@app.post("/guess")
async def guess(item: Guess):
    
    df = pd.DataFrame(data=app.nft_obj)
    df, used_col, ans, state = find_two(df,item.question, item.answer)

    if state:
        result = Answer(state = "Done", question=used_col, answer=ans)
        result.name = df.name.values.tolist()
        result.img = df.img.values.tolist()
        result.tokenId = df.tokenId.values.tolist()
    else:
        result = Answer(state = "Pending", question=used_col, answer=ans)

    return result
