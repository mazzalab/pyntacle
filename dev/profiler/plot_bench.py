import matplotlib.pyplot as plt
import pandas as pd

def create_topdown_menu_plot():


    df = pd.read_csv("./results/times_test.tsv", sep='\t', index_col=[0,1,2,3]).mean(axis=1)
    print(df)

    # Create subplots with 2 rows and 2 columns
    fig, axes = plt.subplots(2, 3, figsize=(12, 4))
    print(axes)
    
    # Add traces to each subplot
    operations = df.index.get_level_values(0)
    k_size = df.index.get_level_values(1)
    nodes = df.index.get_level_values(2)
    edges = df.index.get_level_values(3)
    time = df.values
    colors = ['red', 'blue', 'green', 'black'] 

    # Plot XvsTime per K
    for j, k in enumerate(k_size.unique()):
        for i, oper in enumerate(operations.unique()):
            
            x = edges[(df.index.get_level_values(0) == oper) & (df.index.get_level_values(1) == k)]         # Nodes or Edges
            y = time[(df.index.get_level_values(0) == oper) & (df.index.get_level_values(1) == k)]          # Time

            axes[0][j].plot(x, y, label=oper, color=colors[i])
            
            # Add labels and title
            axes[0][j].set_xlabel('Edges')
            axes[0][j].set_ylabel('Time (s)')
            axes[0][j].set_title(f'Time vs Nodes per Operation (k = {k})')
            axes[0][j].grid(True, color='gray', linestyle='--', linewidth=0.6, alpha=0.3)
            
            # Add legend
            axes[0][j].legend()

    # Plot KvsTime per edges
    for j, edge in enumerate(edges.unique()):
        for i, oper in enumerate(operations.unique()):
            
            x = k_size[(df.index.get_level_values(0) == oper) & (df.index.get_level_values(3) == edge)]         # Nodes or Edges    
            y = time[(df.index.get_level_values(0) == oper) & (df.index.get_level_values(3) == edge)]          # Time

            axes[1][j].plot(x, y, label=oper, color=colors[i])
            
            # Add labels and title
            axes[1][j].set_xlabel('k_size')
            axes[1][j].set_ylabel('Time (s)')
            axes[1][j].set_title(f'Time vs K per Operation (edges = {edge})')
            axes[1][j].grid(True, color='gray', linestyle='--', linewidth=0.6, alpha=0.3)
            
            # Add legend
            axes[1][j].legend()


    # Adjust spacing between subplots (optional)
    plt.tight_layout()

    # Show the plot
    plt.show()

create_topdown_menu_plot()