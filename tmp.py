# %%
import functions as f
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
# Création du csv avec toutes les transactions d'un bloc

# %%
current_index = 3153040
while(True):
    try:
        if current_index < f.MAX_HEIGHT: 
            f.read_tx_csv(current_index)
    except KeyboardInterrupt:
        break
    except:
        print(f'problem at: {current_index}')
    current_index+=1    


# %%
current_height = f.MIN_HEIGHT+6000
f.check_key_offsets(current_height, current_height+1000)
print(f"Done from {current_height} to {current_height+1000}")

# %% [markdown]
# Ajouter les cas pre rct

# %%
height = 1153042
block = f.get_block(height=height)
key_offsets = f.read_keys_and_keyoffsets(set())
#txs = f.read_tx_csv(2148758)
edges = []
nodes_style = {}
all_txs = {}
all_adr = {}
f.get_edges_labels_txs(1153042, f.read_keys_and_keyoffsets(set()), f.get_blackball_adress(), edges, nodes_style, all_txs, all_adr)

tx = eval(read_tx_csv(3153041)[24][3])
tx_inputs_rct_v1 = []
tx_inputs = []
for entry in range(len(tx)):
    if tx[entry][0] != 0:
        tx_inputs_rct_v1.append(tx[entry])
    else:
        tx_inputs += [i for i in tx[entry][1]]
tx_inputs_rct_v1 = [dict_input['key'] for dict_input in get_info_output([convert_keyoffset_to_request(index=input_rct_v1[1][0], amount=input_rct_v1[0]) for input_rct_v1 in tx_inputs_rct_v1])['outs']]


# %% [markdown]
# Test des graphes

# %%
net = Network(notebook=True)
net.add_nodes([1, 2,  3])
net.add_edges([(1, 2, {'color': 'red'}), (2, 3, {'color': 'green'})])
net.show_buttons(filter_=['physics'])
net.options.interaction = {'hideEdgesOnDrag': False, 'hideNodesOnDrag': True, 'dragNodes': True}
net.write_html("ex.html")

# %%
G=networkx.DiGraph()
G.add_nodes_from([(1, {'color': 'green', 'shape': 'square'}), (2, {'color': 'blue'}), (4, {'color': 'red'})])
G.add_edges_from([(1, 2, {'color': 'green'}),(2, 4, {'color': 'blue'}), (4, 1, {'color': 'red'})])
net = Network(height='500px', width='80%', bgcolor='#ffffff', # Changed height
                       font_color='black', notebook=True, directed=True)
net.from_nx(G, node_size_transf= lambda x: x/2, default_node_size=10)
net.show_buttons(filter_=['physics'])
net.options.interaction = {
    'multiselect': True,
    'hideEdgesOnDrag': True, 
    'hideNodesOnDrag': False, 
    'dragNodes': True,
    'hover': True
}
net.write_html(name="Test.html")


# %% [markdown]
# Dessin du graphe

# %%
edges, nodes, all_txs, all_adr, graph = f.draw_from_to(f.MIN_HEIGHT, f.MIN_HEIGHT+720, min_mixing=30)

# %% [markdown]
# Test des limites et vérif de blackball

# %%
print(len(graph.edges), len(graph.nodes), len(edges), len(nodes))

# %%
begin = f.MIN_HEIGHT #3141500
end = begin+720
#f.check_key_offsets(begin, end)
edges, nodes, nodes_style, all_txs, all_adr = f.create_edges_labels_txs(begin, end)

# %%
print(len(edges), len(nodes), len(nodes_style), len(all_txs), len(all_adr))

# %%
nodes_set = f.keep_relevant_inputs(all_adr, nodes_style)
keep_edges = f.keep_relevant_edges(nodes_set, edges)
hash_nodes = set()
for adr in nodes_set:
    hash_nodes.update(all_adr[adr])
nodes_set = nodes_set.union(hash_nodes)
nodes = [(hash_node, nodes_style[hash_node]) for hash_node in nodes_set]
print(len(nodes), len(keep_edges))

# %% [markdown]
# Fonctions auxilliaires aux adresses

# %%
key_offsets = f.read_keys_and_keyoffsets(set())
txs = f.read_tx_csv(3139131)

# %%
out = [f.convert_keyoffset_to_request(keyoffset) for keyoffset in  eval(txs[0][3])[0][1]]
f.get_info_output(out=out)['outs']

# %% [markdown]
# Stats

# %%
# Liste de noms possibles (exemple)
#noms_possibles = list(all_txs.keys())

# Exemple de données pour les tableaux de bord
data = {
    "Alice": {"age": 25, "score": [50, 60, 70]},
    "Bob": {"age": 30, "score": [60, 70, 80]},
    "Charlie": {"age": 35, "score": [70, 80, 90]},
    "David": {"age": 40, "score": [80, 90, 100]},
    "Emma": {"age": 45, "score": [90, 100, 110]},
    "Frank": {"age": 50, "score": [100, 110, 120]},
    "Grace": {"age": 55, "score": [110, 120, 130]},
    "Henry": {"age": 60, "score": [120, 130, 140]},
    "Ivy": {"age": 65, "score": [130, 140, 150]},
    "Jack": {"age": 70, "score": [140, 150, 160]}
}

# Création de l'application Dash
app = dash.Dash(__name__)

# Définition de la mise en page de l'application
app.layout = html.Div([
    dcc.Input(
        id='input-text', 
        type='text', 
        placeholder='Entrez un nom...'
    ),
    html.Button('Rechercher', id='search-button', n_clicks=0),
    html.Div(id='output-div'),
    html.Div(id='selected-name', style={'marginTop': '20px', 'fontWeight': 'bold'}),
    html.Div(id='dashboard')
])

# Callback pour mettre à jour la liste des noms affichés
@app.callback(
    Output('output-div', 'children'),
    [Input('search-button', 'n_clicks')],
    [State('input-text', 'value')]
)
def update_output(n_clicks, value):
    if not value:
        return ''
    value = value.lower()
    filtered_names = [name for name in data.keys() if value in name.lower()]
    return html.Ul([html.Li(name, id={'type': 'name-item', 'index': idx}) for idx, name in enumerate(filtered_names)])

# Callback pour gérer le clic sur un nom et afficher le tableau de bord
@app.callback(
    [Output('selected-name', 'children'),
     Output('dashboard', 'children')],
    [Input({'type': 'name-item', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State({'type': 'name-item', 'index': dash.dependencies.ALL}, 'children')]
)
def display_selected_name_and_dashboard(n_clicks, names):
    if not n_clicks or not any(n_clicks):
        return "Sélectionnez un nom", ""
    selected_name_index = next(i for i, n in enumerate(n_clicks) if n)
    selected_name = names[selected_name_index]
    
    # Génération du contenu du tableau de bord
    person_data = data[selected_name]
    age = person_data['age']
    scores = person_data['score']
    
    # Création du graphique
    df = pd.DataFrame({'Scores': scores, 'Index': range(1, len(scores) + 1)})
    fig = px.line(df, x='Index', y='Scores', title=f'Scores pour {selected_name}')
    
    dashboard_content = html.Div([
        html.H2(f"Tableau de bord pour {selected_name}"),
        html.P(f"Âge: {age}"),
        dcc.Graph(figure=fig)
    ])
    
    return f'Nom sélectionné: {selected_name}', dashboard_content

# Exécution de l'application
if __name__ == '__main__':
    app.run_server(debug=True)




# %%
fig, ax = plt.subplots()

fruits = ['apple', 'blueberry', 'cherry', 'orange']
counts = [40, 100, 30, 55]
bar_labels = ['red', 'blue', '_red', 'orange']
bar_colors = ['tab:red', 'tab:blue', 'tab:red', 'tab:orange']

ax.bar(fruits, counts, label=bar_labels, color=bar_colors)

ax.set_ylabel('fruit supply')
ax.set_title('Fruit supply by kind and color')
ax.legend(title='Fruit color')

# %%



