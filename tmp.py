# %%
#Fichiers internes au projet
import functions as f
import timestamp as ts

#Bibliothèque externe au projet
import requests, json, networkx, csv
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import dash
import plotly.express as px
from pyvis.network import Network
from dash import dcc, html
from dash.dependencies import Input, Output, State



# %%
current_height = f.MIN_HEIGHT+13000
f.check_key_offsets(current_height, current_height+1000)
print(f"Done from {current_height} to {current_height+1000}")

# %% [markdown]
# Création du graphe et de la page html

# %%
edges, nodes, all_txs, all_adr, graph = f.draw_from_to(f.MIN_HEIGHT, f.MIN_HEIGHT+720, min_mixing=30)
print(len(graph.edges), len(graph.nodes), len(edges), len(nodes))
# %% [markdown]
# Test des limites et vérif de blackball
# %%
begin = f.MIN_HEIGHT #3141500
end = begin+720
#f.check_key_offsets(begin, end)
edges, nodes, nodes_style, all_txs, all_adr = f.create_edges_labels_txs(begin, end)
print(len(edges), len(nodes), len(nodes_style), len(all_txs), len(all_adr))
# %% [markdown]

# Stats
def get_stats(hash:str):

    #Stats: calcul la distribution des mixeurs par année
    def calcul_stats(blocks_height, mixings_hash):
        #stats: compteur pour chaque année pour voir la distribution des timestamps des mixeurs
        count_distribution = np.zeros(len(ts.DISTRIBUTION_YEAR))
        #Liste de tuples (hash mixeur, année)
        hash_and_years = {ts.timestamp_to_date(timestamp).year: [] for timestamp in ts.DISTRIBUTION_YEAR}

        #Pour chaque hauteur de mixeur, faire une requête pour récupérer la timestamp
        for index in range(len(blocks_height)):
            #Requête json
            request = {"jsonrpc":"2.0",
                    "id":"0",
                    "method":"get_block_header_by_height",
                    "params":{
                        "height": blocks_height[index]
                        }
                    }
            #requête pour récupérer l'en-tête du bloc
            block_header = requests.post(f.MAIN_URL+'/json_rpc', json=request).json()['result']['block_header']
            #Calcul correct du timestamp de la hauteur actuelle
            mixing_timestamp = block_header['timestamp']-3600*2
            #Ajout à hash_and_years
            hash_and_years[ts.timestamp_to_date(mixing_timestamp).year].append(mixings_hash[index])
            #Ajout au compteur count_distribution
            i = 0
            #incrémenté à l'année suivante si le timestamp du mixeur est plus grand
            while ts.DISTRIBUTION_YEAR[i+1] < mixing_timestamp:
                i+=1
            count_distribution[i]+=1
        return hash_and_years, count_distribution

    #Vérifier si hash est une transaction
    if hash in all_txs:
        print("Requêtes sur les entrées en cours...")
        #Info de la tx
        tx_json = eval(f.get_info_tx(hash)['txs'][0]['as_json'])
        #Keyoffset de chaque entrées mixeur
        mixs_offset = []

        #Pour chaque entré, ajouter les keyoffsets des entrées mixeur de l'entré à mixs_offset
        for entry in tx_json['vin']:
            #Calcul correct de chaque entré mixeur, le ième mixeur est la somme de ses précédents + lui même
            correct_keyoffsets = []
            sum = 0
            for mix_of_entry in entry['key']['key_offsets']:
                sum += mix_of_entry
                correct_keyoffsets.append(sum)
            #Ajout à mixs_offset
            mixs_offset += correct_keyoffsets
        #Requête au noeud pour toutes les keyoffsets
        mixings = f.get_info_output(mixs_offset)['outs']
        #Pour chaque entrée mixeur récupérer: la hauteur, le hash
        blocks_height = []
        mixings_hash = []
        for mixing in mixings:
            #Récupération des infos
            blocks_height.append(mixing['height'])
            mixings_hash.append(mixing['key'])
        
        print("Calcul des stats...")
        #Appel à la fonction calcul_stats
        hash_and_years, count_distribution_year = calcul_stats(blocks_height=blocks_height, mixings_hash=mixings_hash)

        print("Calcul des graphiques...")
        #Figure de matplotlib pour la stat de distribution
        fig, ax = plt.subplots()
        years = [ts.timestamp_to_date(ts_dist).year for ts_dist in ts.DISTRIBUTION_YEAR]
        ax.bar(years, count_distribution_year)
        ax.set_title("Distribution des dates de chaque mixeur de la transaction par année:\n"+hash+"\n")
        ax.set_xlabel("Années")
        ax.set_ylabel("Nombres de mixeurs par date")
        plt.show()
        print(f"Hash de la transaction: {hash}")
        return hash_and_years
    else:
        print("NOT IMPLEMENTED: input or output")

hash = f.get_adress(pre_adr="97cda0ed", l=list(nodes_style.keys()))[0]
hash_and_year = get_stats(hash=hash)
