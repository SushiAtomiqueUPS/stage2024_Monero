import functions as f


def main():
    edges, nodes, all_txs, all_adr, graph = f.draw_from_to(f.MIN_HEIGHT, f.MIN_HEIGHT+720, min_mixing=30)

main()