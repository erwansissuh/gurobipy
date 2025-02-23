import sys
import gurobipy as gp
from gurobipy import GRB
import random
 
def read_input(file_path):
    """Lit le fichier et retourne une liste de photos avec leurs tags."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
   
    N = int(lines[0].strip())
    photos = []
    vertical_photos = []
   
    for i in range(1, N + 1):
        parts = lines[i].strip().split()
        orientation = parts[0]
        tags = set(parts[2:])
       
        if orientation == 'H':
            photos.append(([i - 1], tags))
        else:
            vertical_photos.append((i - 1, tags))
   
    vertical_photos.sort(key=lambda x: len(x[1]), reverse=True)
    while len(vertical_photos) > 1:
        p1 = vertical_photos.pop()
        p2 = vertical_photos.pop()
        photos.append(([p1[0], p2[0]], p1[1] | p2[1]))
   
    return photos
 
def compute_interest(tags1, tags2):
    """Calcule l'intérêt entre deux diapositives."""
    return min(len(tags1 & tags2), len(tags1 - tags2), len(tags2 - tags1))
 
def create_optimized_slideshow(photos):
    """Utilise Gurobi pour générer une solution optimale et en extraire l'ordre."""
    model = gp.Model("slideshow")
    model.setParam(GRB.Param.TimeLimit, 600)
    model.setParam(GRB.Param.MIPGap, 1e-9)
   
    S = len(photos)
    x = model.addVars(S, S, vtype=GRB.BINARY, name="x")
   
    # Objectif : maximiser la somme des intérêts entre les diapositives consécutives
    model.setObjective(
        gp.quicksum(compute_interest(photos[i][1], photos[j][1]) * x[i, j]
                    for i in range(S) for j in range(S) if i != j),
        GRB.MAXIMIZE
    )
   
    # Contraintes : chaque diapositive doit avoir exactement un prédécesseur et un successeur
    for i in range(S):
        model.addConstr(gp.quicksum(x[i, j] for j in range(S) if i != j) == 1)
        model.addConstr(gp.quicksum(x[j, i] for j in range(S) if i != j) == 1)
   
    # Ajouter des contraintes pour éliminer les sous-tours
    u = model.addVars(S, vtype=GRB.CONTINUOUS, name="u")
    for i in range(1, S):
        for j in range(1, S):
            if i != j:
                model.addConstr(u[i] - u[j] + S * x[i, j] <= S - 1)
   
    model.optimize()
   
    if model.Status == GRB.OPTIMAL:
        print(f"✅ Solution optimale trouvée avec un score de {model.ObjVal}")
        slideshow = extract_slideshow_from_gurobi(x, photos, S)
        return slideshow, model.ObjVal
    else:
        print("⚠ Gurobi n'a pas trouvé de solution optimale.")
        return [], 0
 
def extract_slideshow_from_gurobi(x, photos, S):
    """Extrait le diaporama à partir des variables binaires de Gurobi."""
    slideshow_order = []
    current = 0  # Commencer par la première diapositive
   
    for _ in range(S):
        slideshow_order.append(sorted(photos[current][0]))
        # Trouver la prochaine diapositive
        for j in range(S):
            if current != j and x[current, j].X > 0.5:
                current = j
                break
   
    return slideshow_order
 
def analyze_transitions(slideshow_order, photos_dict):
    """Calcule le score total du diaporama."""
    total_score = 0
    for i in range(len(slideshow_order) - 1):
        score = compute_interest(
            photos_dict[tuple(slideshow_order[i])],
            photos_dict[tuple(slideshow_order[i + 1])]
        )
        total_score += score
    return total_score
 
def write_output(file_path, slideshow_order):
    """Sauvegarde la solution finale."""
    with open(file_path, 'w') as f:
        f.write(f"{len(slideshow_order)}\n")
        for slide in slideshow_order:
            f.write(" ".join(map(str, slide)) + "\n")
 
def main():
    if len(sys.argv) != 2:
        print("Usage: python slideshow.py <input_file>")
        return
   
    input_file = sys.argv[1]
    photos = read_input(input_file)
    photos_dict = {tuple(sorted(photo[0])): photo[1] for photo in photos}
   
    slideshow_order, optimal_score = create_optimized_slideshow(photos)
   
    if slideshow_order:
        final_score = analyze_transitions(slideshow_order, photos_dict)
        print(f"✅ Score final atteint : {final_score}")
        write_output("slideshow.sol", slideshow_order)
        print("✅ Solution finale enregistrée.")
    else:
        print("⚠ Aucune solution n'a été trouvée.")
 
if __name__ == "__main__":
    main()