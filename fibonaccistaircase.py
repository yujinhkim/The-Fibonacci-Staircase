import streamlit as st
import numpy as np
import plotly.graph_objects as go

def generate_fibonacci(count):
    """Generates the first 'count' Fibonacci numbers using float64 to delay overflow."""
    fibs = np.zeros(count, dtype=np.float64)
    if count > 0: fibs[0] = 1
    if count > 1: fibs[1] = 1
    for i in range(2, count):
        fibs[i] = fibs[i-1] + fibs[i-2]
    return fibs

def create_snaking_grids(N):
    """Returns the Fibonacci heights and the sequence index for the even color gradient."""
    total_numbers = N**2
    fibs = generate_fibonacci(total_numbers)
    h_grid = np.zeros((N, N), dtype=np.float64)
    color_grid = np.zeros((N, N), dtype=np.float64)
    
    idx = 0
    for y in range(N):
        if y % 2 == 0:
            for x in range(N):
                h_grid[y, x] = fibs[idx]
                color_grid[y, x] = idx + 1
                idx += 1
        else:
            for x in range(N-1, -1, -1):
                h_grid[y, x] = fibs[idx]
                color_grid[y, x] = idx + 1
                idx += 1
    return h_grid, color_grid

def format_fib_label(val):
    """Formats large Fibonacci numbers so they don't visually overlap and clutter."""
    if val >= 1e6:
        return f"{val:.2e}"  
    else:
        return str(int(val)) 

def build_voxel_mesh(h, c, use_log):
    """Constructs the 3D blocky mesh and calculates floating text coordinates."""
    N = h.shape[0]
    vertices = []
    i_faces, j_faces, k_faces = [], [], []
    vertex_colors = []
    
    text_x, text_y, text_z, text_labels = [], [], [], []
    
    v_idx = 0
    for y in range(N):
        for x in range(N):
            H = h[y, x]
            C = c[y, x] 
            
            x0, x1 = x - 0.5, x + 0.5
            y0, y1 = y - 0.5, y + 0.5
            
            z0 = 0
            if use_log:
                z1 = np.log10(H) + 1 if H > 0 else 0
            else:
                z1 = H
                
            text_x.append(x)
            text_y.append(y)
            text_z.append(z1) 
            text_labels.append(format_fib_label(H))
            
            box_verts = [
                [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], 
                [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]  
            ]
            vertices.extend(box_verts)
            vertex_colors.extend([C] * 8)
            
            faces = [
                [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7], 
                [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6], 
                [0, 3, 7], [0, 7, 4], [1, 2, 6], [1, 6, 5]  
            ]
            
            for tri in faces:
                i_faces.append(tri[0] + v_idx)
                j_faces.append(tri[1] + v_idx)
                k_faces.append(tri[2] + v_idx)
                
            v_idx += 8
            
    if not vertices:
        return [], [], [], [], [], [], [], [], [], [], []
        
    vx, vy, vz = zip(*vertices)
    return vx, vy, vz, i_faces, j_faces, k_faces, vertex_colors, text_x, text_y, text_z, text_labels

# ==========================================
# STREAMLIT APPLET UI
# ==========================================

st.set_page_config(page_title="Feel better Dr. Park!", layout="centered")

st.title("The Fibonacci Staircase")

N = st.number_input(
    "Choose N, and I'll show you the first N^2 Fibonacci numbers", 
    min_value=1, 
    max_value=12,  
    value=5, 
    step=1
)

use_log = st.checkbox("Click to plot using a logarithmic scale")
# NEW: Checkbox to toggle the labels on and off (defaults to True)
show_labels = st.checkbox("Show the numbers", value=True)

st.divider()

(vx, vy, vz, i_faces, j_faces, k_faces, vertex_colors, 
 text_x, text_y, text_z, text_labels) = build_voxel_mesh(*create_snaking_grids(N), use_log)

if use_log:
    colorscale = 'Blues' 
    z_title = "Log10(Height) + 1"
    plot_title = f"Fibonacci Staircase (first {N**2} Fibonacci numers)"
    aspect_mode = 'auto' 
    aspect_ratio = None
else:
    colorscale = 'Plasma' 
    z_title = "True Height"
    plot_title = f"Fibonacci Staircase (first {N**2} Fibonacci numers)"
    aspect_mode = 'manual'
    aspect_ratio = dict(x=1, y=1, z=0.6) 

mesh = go.Mesh3d(
    x=vx, y=vy, z=vz,
    i=i_faces, j=j_faces, k=k_faces,
    intensity=vertex_colors,
    colorscale=colorscale,     
    intensitymode='vertex',
    flatshading=True,         
    showscale=True,
    colorbar=dict(
        title=dict(text="Sequence Step", font=dict(color="black")), 
        thickness=15, 
        len=0.7, 
        tickfont=dict(color="black") 
    ),
    lighting=dict(ambient=0.4, diffuse=0.8, specular=1.5, roughness=0.1, fresnel=0.2)
)

# Set up the data list with our primary mesh
plot_data = [mesh]

# Conditionally add the text trace if the user checked the box
if show_labels:
    text_trace = go.Scatter3d(
        x=text_x, y=text_y, z=text_z,
        mode='text',
        text=text_labels,
        textposition='top center', 
        textfont=dict(color='black', size=12, family="Arial Black"),
        showlegend=False,
        hoverinfo='skip' 
    )
    plot_data.append(text_trace)

# Pass the conditional list to the Figure
fig = go.Figure(data=plot_data)

fig.update_layout(
    title=plot_title,
    scene=dict(
        xaxis=dict(title="X", visible=False),
        yaxis=dict(title="Y", visible=False),
        zaxis=dict(title=z_title, backgroundcolor='#EAEAEA', gridcolor='#CCCCCC'),
        aspectmode=aspect_mode,
        aspectratio=aspect_ratio
    ),
    margin=dict(l=0, r=0, b=0, t=50),
    paper_bgcolor='#F5F5F5', 
    font=dict(color='black'),
    height=600 
)

st.plotly_chart(fig, use_container_width=True)
