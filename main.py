import functions as f
import stats 


def main():
    def create_graph():
        print("\n-------------------------------------")
        print("Choisir un intervalle de bloc pour le graphe:")
        begin = input("Hauteur du premier bloc: ")
        end = input("Hauteur du dernier bloc: ")
        min_mixing = input("Nombre de transactions minimums incluant un mixeur: ")
        edges, nodes, all_txs, all_adr, graph = f.draw_from_to(begin=int(begin), end=int(end), min_mixing=int(min_mixing))
        return edges, nodes, all_txs, all_adr, graph
    
    edges, nodes, all_txs, all_adr, graph = create_graph()
    choice = ""
    while choice != "quit":
        print("\n-------------------------------------")
        choice = input("Les choix possibles sont : quit, stat, create_graph\n")
        
        if choice == "quit":
            break
        elif choice == "stat":
            print("\n-------------------------------------")
            pre_hash = input("Premiers caractères du hash de la transaction: ")
            hash = f.get_adress(pre_adr=pre_hash, l=all_txs.keys())
            while len(hash) > 1:
                print(f"Les transactions candidates sont :\n{hash}")
                pre_hash = input("Ajoutez plus de caractères: ")
                hash = f.get_adress(pre_adr=pre_hash, l=all_txs.keys())
            print("Pour poursuivre l'exécution, il faudra fermer la fenêtre avec les stats affichées")
            tmp = stats.get_stats(hash=hash[0], dict_txs=all_txs)
        elif choice == "create_graph":
            edges, nodes, all_txs, all_adr, graph = create_graph()

main()