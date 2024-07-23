import requests, json, networkx, csv, os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import dash
import plotly.express as px
from pyvis.network import Network
from dash import dcc, html
from dash.dependencies import Input, Output, State

#Monero public nodes url
MAIN_URL = 'http://node.monerodevs.org:18089'#'http://node.xmr.rocks:18089'
TEST_URL = 'http://node2.monerodevs.org:28089'
STAGE_URL = 'http://node.monerodevs.org:38089' 
url = MAIN_URL
MIN_HEIGHT = 3139000
MAX_HEIGHT = 3161280

# Chemin absolu vers le fichier dans le dossier Data
DATA_FILE_FROM_PATH = os.path.join(os.path.dirname(os.path.abspath('tmp.py')), "..", "Data")


"""
Make JSON request and return it
"""
def make_json_request(request: dict, method: str, url=MAIN_URL):
    if method == 'get_block':
        if url.split('/')[len(url.split('/'))-1] != 'json_rpc':
            return requests.post(url+'/json_rpc', json=request).json().get('result')
        else:
            return requests.post(url, json=request).json().get('result')
    elif method == 'get_tx':
        if url.split('/')[len(url.split('/'))-1] != 'get_transactions':
            return requests.post(url+'/get_transactions', json=request).json()
        else:
            return requests.post(url, json=request).json()
    elif method == 'get_output':
        if url.split('/')[len(url.split('/'))-1] != 'get_outs':
            return requests.post(url+'/get_outs', json=request).json()
        else:
            return requests.post(url, json=request).json()
        
"""
Given an hash of a tx, return his JSON request
"""
def get_info_tx(tx, url=MAIN_URL):
    if isinstance(tx, list):
        request = {
            "txs_hashes": tx, 
            "decode_as_json": True
        }
    else:
        request = {
            "txs_hashes": [tx], 
            "decode_as_json": True
        }
    return make_json_request(request, 'get_tx')



"""
Convert a JSON request to a Serie
"""
def json_result_to_serie(request_result: dict, method: str)->pd.Series:
    if method == 'from_node':
        tmp = request_result['block_header'].copy()
        try:
            tmp['tx_hashes'] = request_result['tx_hashes'].copy()
        except KeyError: 
            print(f'Transaction not found in block: {request_result['block_header']['height']}')
            tmp['tx_hashes'] = []
        return pd.Series(data=tmp)
    elif method == 'from_excel':
        return pd.Series(data=request_result)

"""
Get the block of height from the node url 
"""
def get_block(height: int, url=MAIN_URL):
    #Create JSON request
    request = {
                'jsonrpc':'2.0',
                'id':'0',
                'method':'get_block',
                'params': {
                    'height': height
                    }
                }
    #Make request to url, convert to a serie then return it
    return json_result_to_serie(make_json_request(request, request['method'], url=MAIN_URL), 'from_node')

def convert_keyoffset_to_request(index, amount=0):
        return {"index": index, "amount": amount}

def write_keyoffsets(key_offsets: set, filename = DATA_FILE_FROM_PATH+'/keyoffsets_to_adress.csv'):
    #Init des variables: nb d'objets max par requêtes, liste de toutes les keyoffsets, un indice i et une liste result 
    max_requests_index = 1000
    all_key_offsets_list = list(key_offsets)
    i = 0
    result = []

    #Tant qu'il reste des requêtes à faire, on les fait pour les keyoffsets de [1000*i, 1000*(i+1)]
    while len(key_offsets)>max_requests_index*(i+1):
        #Requêtes au noeud pour charger les clés correspondantes aux keyoffsets et ajout à la liste result
        tmp = all_key_offsets_list[max_requests_index*i:max_requests_index*(i+1)]
        result += get_info_output(out=[convert_keyoffset_to_request(keyoffset) for keyoffset in tmp])['outs']
        i+=1
    tmp=all_key_offsets_list[max_requests_index*i:len(all_key_offsets_list)]
    result += get_info_output(out=[convert_keyoffset_to_request(keyoffset) for keyoffset in tmp])['outs']
    
    #Écriture des clés récupéré (result) vers un fichier csv 
    all_keys = {}
    with open(filename, 'a') as f:
            for index in range(len(result)):
                #keyoffset; clé; (mask non intégré) 
                f.write(str(all_key_offsets_list[index]) + ';' + result[index]['key']  + '\n') #+ ';' + result['outs'][index]['mask']
                all_keys[all_key_offsets_list[index]] = result[index]['key']
    return all_keys

def read_keys_and_keyoffsets(key_offsets: set):
    all_keys = {}
    tmp = set()
    filename = DATA_FILE_FROM_PATH+'/keyoffsets_to_adress.csv'
    try:
        with open(filename, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            for i, row in enumerate(reader):
                all_keys[int(row[0])] = row[1]
                tmp.add(int(row[0]))  
        key_offsets_to_write = key_offsets.difference(tmp)
        if len(key_offsets_to_write) > 0:
            return write_keyoffsets(key_offsets_to_write).update(all_keys)
        else: 
            return all_keys
    except FileNotFoundError:
        return write_keyoffsets(key_offsets)

def check_key_offsets(begin, end):
    all_key_offsets = set()
    for height in range(begin, end+1):
        filename = DATA_FILE_FROM_PATH+'/txs/block_'+ str(height) +'_txs.csv'
        with open(filename, 'r') as f:
            read = csv.reader(f, delimiter=';')
            for i, row in enumerate(read):
                if len(row)>0:
                    row.pop()
                    for j in eval(row[3]):
                        all_key_offsets.update(j[1])
    read_keys_and_keyoffsets(all_key_offsets)

def write_tx_csv(rows, filename):
    with open(filename, 'a') as f:
        for row in rows:
            string_list_row = [str(i) for i in row]
            for i in string_list_row:
                f.write(i+"; ")
            f.write("\n")

def read_tx_csv(height):
    col_names = ["tx_hash", "confirmations", "double_spend_seen", "vin", "vout", "extra", "version", "rct_signatures"]
    index_in = col_names.index("vin")
    index_out = col_names.index("vout")
    col_names_outputs = ['amount', 'key', 'view_tag']

    #Convetie une sortie en un tuple pour le csv
    def convert_output_to_tuple(d: dict)->tuple:
            return (d['amount'], d['target']['tagged_key']['key'], d['target']['tagged_key']['view_tag'])

    #Convertie une entrée un en un tuple pour le csv
    def convert_input_to_tuple(d: dict)->tuple:
        correct_key_offsets = []
        sum = 0
        for i in d['key']['key_offsets']:
            sum+=i
            correct_key_offsets.append(sum)
        return (d['key']['amount'], correct_key_offsets, d['key']['k_image']) 


    filename = DATA_FILE_FROM_PATH+'/txs/block_'+ str(height) +'_txs.csv'
    row_read = []
    try:
        with open(filename, 'r') as f:
            read = csv.reader(f, delimiter=';')
            for i, row in enumerate(read):
                if len(row)>0:
                    row.pop()
                row_read.append(row)

    except FileNotFoundError:
        #Récupération des infos du bloc avec une requête json
        block = get_block(height=height)
        #txs = block[height]['tx_hashes'].split(', ')

        #Récupération des infos des transactions avec une requête json
        txs = block['tx_hashes']
        if len(txs) > 99:
            txs_req = get_info_tx(tx=txs[0:99])    
            i = 1
            while len(txs[i*99:]) > 99:
                txs_req['txs'] += get_info_tx(tx=txs[i*99:99*(i+1)])['txs']
                i+=1
            txs_req['txs'] += get_info_tx(tx=txs[i*99:])['txs']
        elif len(txs) <= 0:
            write_tx_csv([], filename=filename)
            return row_read
        else: 
            txs_req = get_info_tx(tx=txs)
        
        #Récupération d'une transaction et formatage pour le csv
        for tx in txs_req['txs']:
            #Init des variables
            row = []
            tx_json = json.loads(tx['as_json'])
            tx_keys = tx_json.keys()

            #Ajout des infos pour chaque noms de colonnes 
            for i in col_names:
                try:
                    row.append(tx[i])
                except KeyError:
                    if i in tx_keys:    
                        row.append(tx_json[i])
            #Conversion des entrées et sorties
            row[index_out] = [convert_output_to_tuple(i) for i in row[index_out]]
            row[index_in] = [convert_input_to_tuple(i) for i in row[index_in]]
            #Ajout de la transaction formater dans une liste
            row_read.append(row)
        #Écriture des toutes les transactions du blocs dans un fichier
        write_tx_csv(row_read, filename=filename)
        #check_key_offsets(MIN_HEIGHT, height)
    return row_read



"""
JSON requests or excel rows into dict of blocks
"""
def get_blocks_from_to(begin:int, end: int, url=MAIN_URL)->dict:
    blocks_dict = {}
    for i in range(begin, end+1):
        blocks_dict[i] = get_block(i, from_file_or_node='from_node')
    assert(len(blocks_dict) == (end-begin)+1)
    return blocks_dict



"""
Given an ouptput index from a json tx, return the json request of the output
"""
def get_info_output(out, url=MAIN_URL):
    if isinstance(out, list):
        request = {"outputs": out}
    else:
        request = {"outputs": [{"index": out, "amount": 0}]}
    return make_json_request(request, 'get_output') 

def get_blackball_adress():
    def read_blackball_pool()->set:
        blackball_adr = set()
        filename =DATA_FILE_FROM_PATH+'/pools.txt' 
        with open(filename, 'r') as f:
            reader = f.readlines()
            for i, row in enumerate(reader):
                blackball_adr.add(row.strip('\n'))
        return blackball_adr

    try:
        blackball_adr = set()
        filename = DATA_FILE_FROM_PATH+"/blackball_keyoffsets_to_adress.csv"
        with open(filename, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            for i, row in enumerate(reader):
                blackball_adr.add(row[1])
        return blackball_adr.union(read_blackball_pool())
    except FileNotFoundError:
        blackball_adr = set()
        filename = DATA_FILE_FROM_PATH+'/rct-only-2019-03-12.txt'
        with open(filename, 'r') as f:
            blackball_adr = set()
            reader = f.readlines()
            for i, row in enumerate(reader):
                if not('*' in row or '@' in row or len(row)<3):
                    blackball_adr.add(int(row.strip('\n')))
        _tmp = write_keyoffsets(blackball_adr, filename= DATA_FILE_FROM_PATH+"/blackball_keyoffsets_to_adress.csv")
        return blackball_adr.union(read_blackball_pool())

#Return edges, labels and txs from a block height and key_offsets, , labels: dict, cpt_in, cpt_out
def get_edges_labels_txs(block_height: int, key_offsets: dict, blackball_adr: set, edges: list, nodes_style: list, all_txs: dict, all_adr:dict):
    #Compteur pour tester
    nb_adr = 0
    #Récupération des infos des transactions du bloc
    txs = read_tx_csv(block_height)
    for tx in txs:
        #Init des variables: le hash, les sorties, les entrées, 
        # une liste pour les entrées avec rct et la liste avec toutes les adresses mixeurs compris de chaque entrée
        tx_hash = tx[0]
        tx_outputs = [i[1] for i in eval(tx[4])]
        nb_adr += len(tx_outputs)
        tx_all_inputs = eval(tx[3])
        tx_all_mixings_spend_inputs = []
        tx_inputs_rct_v1 = []
        for input in range(len(tx_all_inputs)):
            nb_adr += len(tx_all_inputs[input][1])
            if tx_all_inputs[input][0] > 0:
                tx_inputs_rct_v1.append(tx_all_inputs[input])
            else:
                tx_all_mixings_spend_inputs += [key_offsets[i] for i in tx_all_inputs[input][1]]
        if len(tx_inputs_rct_v1) > 0:
            tx_all_mixings_spend_inputs += [dict_input['key'] for dict_input in get_info_output([convert_keyoffset_to_request(index=input_rct_v1[1][0], amount=input_rct_v1[0]) for input_rct_v1 in tx_inputs_rct_v1])['outs']]

        
        #Ajout dans un dictionnaire contenant toutes les txs par hash avec entrée et sorties
        all_txs[tx_hash] = {"in": tx_all_mixings_spend_inputs, "out": tx_outputs}

        #Coloration et ajout des arêtes pour chaque sortie (tx_hash, output)
        for output in tx_outputs:
            if output in blackball_adr:
                color_output = 'black'
            else:
                color_output = 'green'
            output_style = {'color': color_output, 'shape': 'star'}
            edges.append((tx_hash, output, {'color': color_output}))
            nodes_style[output] = output_style
            try:
                l = all_adr[output] 
                if not tx_hash in l:
                    all_adr[output].append(tx_hash)
            except KeyError:
                all_adr[output] = [tx_hash]

        #Coloration et ajout des arêtes pour chaque entrée (input, tx_hash)
        for input in tx_all_mixings_spend_inputs:
            if input in blackball_adr:
                color_input = 'black'
            else:
                color_input = 'red'
            input_style = {'color': color_input, 'shape': 'dot'}
            edges.append((input, tx_hash, {'color': color_input}))
            nodes_style[input] = input_style
            try:
                l = all_adr[input] 
                if not tx_hash in l:
                    all_adr[input].append(tx_hash)
            except KeyError:
                all_adr[input] = [tx_hash]
        
        #Coloration du noeud de la tx_hash
        hash_style = {'color': 'yellow', 'shape': 'square'}
        nodes_style[tx_hash] = hash_style
    #Réfléchir à un test
    #assert(nb_adr==len(edges)) 

def create_edges_labels_txs(begin, end):
    key_offsets = read_keys_and_keyoffsets(set())
    blackball_adr = get_blackball_adress()
    edges = []
    nodes_style = {}
    all_txs = {}
    all_inputs_and_outputs = {}
    for i in range(begin, end):
        get_edges_labels_txs(i, key_offsets, blackball_adr, edges, nodes_style, all_txs, all_inputs_and_outputs)
    nodes = [(node, nodes_style[node]) for node in nodes_style]
    return edges, nodes, nodes_style, all_txs, all_inputs_and_outputs
        

def keep_relevant_edges(keep_txs:set, edges:list):
    keep_edges = []
    for edge in edges:
        if edge[0] in keep_txs or edge[1] in keep_txs:
            keep_edges.append(edge)
    return keep_edges

#Vérification des noeuds à conservés (ceux avec plus d'une tx présent et ceux déclarés comme utilisés)
def keep_relevant_inputs(all_adr, nodes_style, min_mixing):
    nodes = set()
    for adr in all_adr:
        txs_hash = all_adr[adr]
        if len(txs_hash) > min_mixing or nodes_style[adr]['color'] == 'black':
            nodes.add(adr)
    return nodes


def count_adr_in_tx(height):
    sum = 0
    for tx in read_tx_csv(height):
        for entry in eval(tx[3]):
            sum+=len(entry[1])
        sum += len(eval(tx[4]))
    return sum

def draw_from_to(begin, end, url=MAIN_URL, min_mixing = 5):
    if end-begin >= 0:
        # Chargement des bloc de hauteur begin à end inclus
        #blocks = get_blocks_from_to(begin, end, method='from_node')

        all_edges, all_nodes, all_nodes_colors, all_txs, all_adr = create_edges_labels_txs(begin, end)
        
        #Filtrage des noeuds
        nodes_set = keep_relevant_inputs(all_adr, all_nodes_colors, min_mixing)
        
        #Filtrage des arêtes
        keep_edges = keep_relevant_edges(nodes_set, all_edges)

        #Ajout du hash des transactions
        hash_nodes = set()
        for adr in nodes_set:
            hash_nodes.update(all_adr[adr])
        nodes_set = nodes_set.union(hash_nodes)
        keep_nodes = [(hash_node, all_nodes_colors[hash_node]) for hash_node in nodes_set]

        #keep_nodes = all_nodes
        #keep_edges = all_edges
        # Création d'un fichier html du graphe avec toutes les transactions du bloc 3159524
        G=networkx.DiGraph()
        G.add_nodes_from(keep_nodes)
        G.add_edges_from(keep_edges)
        print("pass making edges and G")
        
        net = Network(height='500px', width='80%', bgcolor='#ffffff', # Changed height
                        font_color='black', notebook=True, directed=True, neighborhood_highlight=True)
        net.toggle_physics(False)
        net.toggle_stabilization(True)
        net.force_atlas_2based(overlap=0.80)
        net.from_nx(G, default_node_size=20)
        net.options.interaction = {
            'multiselect': True,
            'hideEdgesOnDrag': True, 
            'hideNodesOnDrag': False, 
            'dragNodes': True,
            'hover': True
        }
        
        net.show_buttons(filter_=['physics'])
        net.write_html("Monero_graph.html")

        print("pass making net")
        return keep_edges, keep_nodes, all_txs, all_adr, net
    else: 
        raise IndexError(f'end={end} < begin={begin}')