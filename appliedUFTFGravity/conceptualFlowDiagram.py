import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

def create_glm_entropy_diagram_final_fixed():
    """
    Generates a conceptual flow diagram illustrating the connection between
    Bekenstein-Hawking Entropy, L1-Integrability (LIC/ACI), and the
    Gelfand-Levitan-Marchenko (GLM) Inverse Scattering Transform, with
    improved layout and highly readable text.
    """
    # Initialize the plot
    fig, ax = plt.subplots(figsize=(18, 10)) # Keep increased figure size
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect('equal')
    ax.axis('off')

    # Define colors
    COLOR_A = '#2a64ad'  # Dark Blue (Foundational Constraint)
    COLOR_B = '#ff6347'  # Tomato Red (Mathematical Condition)
    COLOR_C = '#4c9a2a'  # Green (Analytic Tool)
    COLOR_D = '#7f00ff'  # Purple (Physical Outcome)
    TEXT_COLOR = 'white'
    ARROW_COLOR = '#333333'

    # Box dimensions and layout
    box_width = 25  # Slightly increased width again
    box_height = 25 # SIGNIFICANTLY increased height for multi-line text
    y_level = 50
    
    # Adjusted x_positions for the new width and better spacing
    x_positions = [13, 38, 63, 88] 
    
    # Text font size
    FONT_SIZE = 8 # Reduced font size for better fit

    # --- Nodes ---

    # 1. Finite Bekenstein-Hawking Entropy (The Physical Constraint)
    node1_text = r'Finite Bekenstein-Hawking Entropy' + '\n' + r'$S_{\text{BH}} < \infty$'
    rect1 = Rectangle((x_positions[0] - box_width/2, y_level - box_height/2), box_width, box_height, facecolor=COLOR_A, edgecolor=ARROW_COLOR, linewidth=2, label='Physical Constraint')
    ax.add_patch(rect1)
    ax.text(x_positions[0], y_level, node1_text, color=TEXT_COLOR, ha='center', va='center', fontsize=FONT_SIZE, weight='bold')

    # 2. L1-Integrability Condition (The Mathematical Equivalence)
    node2_text = r'L$^1$-Integrability Condition (LIC)' + '\n' + r'$||\Psi_{\text{horizon}}||_{L^1} < \infty$'
    rect2 = Rectangle((x_positions[1] - box_width/2, y_level - box_height/2), box_width, box_height, facecolor=COLOR_B, edgecolor=ARROW_COLOR, linewidth=2, label='Stability Condition')
    ax.add_patch(rect2)
    ax.text(x_positions[1], y_level, node2_text, color=TEXT_COLOR, ha='center', va='center', fontsize=FONT_SIZE, weight='bold')

    # 3. GLM Inverse Scattering Transform (The Analytic Mechanism)
    # Added extra line breaks here to force the text to fit cleanly inside the wider box
    node3_text = r'Gelfand-Levitan-Marchenko (GLM) ' + '\n' + r'Inverse Scattering Transform'
    rect3 = Rectangle((x_positions[2] - box_width/2, y_level - box_height/2), box_width, box_height, facecolor=COLOR_C, edgecolor=ARROW_COLOR, linewidth=2, label='Analytic Tool')
    ax.add_patch(rect3)
    ax.text(x_positions[2], y_level, node3_text, color=TEXT_COLOR, ha='center', va='center', fontsize=FONT_SIZE, weight='bold')

    # 4. Exact Informational State Recovery (The Unitary Outcome)
    node4_text = r'Exact Informational State Recovery' + '\n' + r'(Unitary Evolution)'
    rect4 = Rectangle((x_positions[3] - box_width/2, y_level - box_height/2), box_width, box_height, facecolor=COLOR_D, edgecolor=ARROW_COLOR, linewidth=2, label='Physical Outcome')
    ax.add_patch(rect4)
    ax.text(x_positions[3], y_level, node4_text, color=TEXT_COLOR, ha='center', va='center', fontsize=FONT_SIZE, weight='bold')


    # --- Arrows and Labels ---

    # Arrow 1 -> 2: Equivalence / Constraint
    arrow1_start_x = x_positions[0] + box_width/2
    arrow1_end_x = x_positions[1] - box_width/2
    
    ax.annotate("", xy=(arrow1_end_x, y_level), xytext=(arrow1_start_x, y_level),
                arrowprops=dict(arrowstyle="<->", color=ARROW_COLOR, lw=3))
    
    # Arrow label position adjusted to ensure it doesn't cross the text on the box edge
    ax.text((arrow1_start_x + arrow1_end_x)/2, y_level + 5, r'Equivalence: GR $\Leftrightarrow$ LIC', ha='center', fontsize=9, color=ARROW_COLOR)
    ax.text(x_positions[1], y_level + box_height/2 + 3, r'Enforced by ACI', ha='center', fontsize=9, color=COLOR_B)

    # Arrow 2 -> 3: Necessary Input Condition
    arrow2_start_x = x_positions[1] + box_width/2
    arrow2_end_x = x_positions[2] - box_width/2
    
    ax.annotate("", xy=(arrow2_end_x, y_level), xytext=(arrow2_start_x, y_level),
                arrowprops=dict(arrowstyle="->", color=ARROW_COLOR, lw=3))
    ax.text((arrow2_start_x + arrow2_end_x)/2, y_level - 5, r'Provides Necessary Spectral Decay', ha='center', fontsize=9, color=ARROW_COLOR)

    # Arrow 3 -> 4: Recovery Mechanism
    arrow3_start_x = x_positions[2] + box_width/2
    arrow3_end_x = x_positions[3] - box_width/2
    
    ax.annotate("", xy=(arrow3_end_x, y_level), xytext=(arrow3_start_x, y_level),
                arrowprops=dict(arrowstyle="->", color=ARROW_COLOR, lw=3))
    ax.text((arrow3_start_x + arrow3_end_x)/2, y_level + 3, r'Reconstruction Kernel $K(x,y)$', ha='center', fontsize=9, color=ARROW_COLOR)

    # Title
    ax.set_title(r'Spectral-Analytic Resolution of the Black Hole Information Paradox', fontsize=16, pad=20, weight='bold')
    ax.text(50, 88, r'Central Role of GLM and $L^1$-Integrability in the UFT-F Framework', ha='center', fontsize=12)

    plt.show()

if __name__ == '__main__':
    create_glm_entropy_diagram_final_fixed()