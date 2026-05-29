import plotly.graph_objects as go
import numpy as np

def get_metal_color(metal_name):
    color_map = {"M1": "blue", "M2": "yellow", "M3": "green", "M4": "grey"}
    return color_map.get(metal_name, "purple")

def render_interactive_grid(rows, cols, h_metal_name, v_metal_name):
    # Set the size of each square unit cell
    cell_size = 2.0 
    
    fig = go.Figure()

    # 1. Draw the Unit Cell Grid (Background) - Forces square proportions
    for r in range(rows + 1):
        fig.add_shape(type="line", x0=0, y0=r*cell_size, x1=cols*cell_size, y1=r*cell_size, line=dict(color="black", width=1))
    for c in range(cols + 1):
        fig.add_shape(type="line", x0=c*cell_size, y0=0, x1=c*cell_size, y1=rows*cell_size, line=dict(color="black", width=1))

    # 2. Draw Metal Stripes
    h_color = get_metal_color(h_metal_name.split('+')[0].strip())
    v_color = get_metal_color(v_metal_name.split('+')[0].strip())

    # Horizontal Bus
    for r in range(rows):
        fig.add_shape(type="rect", x0=0, y0=r*cell_size + 0.5, x1=cols*cell_size, y1=r*cell_size + 1.5,
                      fillcolor=h_color, opacity=0.5, line=dict(width=0))
    
    # Vertical Feeder
    for c in range(cols):
        fig.add_shape(type="rect", x0=c*cell_size + 0.5, y0=0, x1=c*cell_size + 1.5, y1=rows*cell_size,
                      fillcolor=v_color, opacity=0.5, line=dict(width=0))

    fig.update_layout(
        title="LDO Unit Cell Grid (Physical Square Topology)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        height=500
    )
    return fig