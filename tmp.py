# %%
#Fichiers internes au projet
import functions as f
import timestamp as ts
import stats as st

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
# %% [markdown]
# Création du graphe et de la page html

# %%
edges, nodes, all_txs, all_adr, graph = f.draw_from_to(f.MIN_HEIGHT, f.MIN_HEIGHT+720*7, min_mixing=300)
print(len(graph.edges), len(graph.nodes), len(edges), len(nodes))
# %% [markdown]
# Test des limites et vérif de blackball
# %%
begin = f.MIN_HEIGHT #3141500
end = begin+10
#f.check_key_offsets(begin, end)
edges, nodes, nodes_style, all_txs, all_adr = f.create_edges_labels_txs(begin, end)
print(len(edges), len(nodes), len(nodes_style), len(all_txs), len(all_adr))
#%%
st.get_stats(f.get_adress("fd836", nodes_style.keys())[0], all_txs)
# %%

hash = f.get_adress(pre_adr="aeb6a0c", l=list(nodes_style.keys()))[0]
hash_and_year = st.get_stats(hash=hash)

#%%
hash_and_year
# %%
