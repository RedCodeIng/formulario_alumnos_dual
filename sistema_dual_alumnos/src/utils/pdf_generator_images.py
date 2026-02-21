import matplotlib.pyplot as plt
import os

def create_percentage_donut(percentage: int, output_path: str):
    """
    Creates a donut chart representing a percentage, styled similar to
    the DUAL system requirements (Teal/Green for progress, Gray for remaining).
    Saves the output as a PNG file.
    
    Args:
        percentage (int): 0 to 100
        output_path (str): The file path where the image will be saved.
    """
    # Ensure percentages are clamped between 0 and 100
    percentage = max(0, min(100, percentage))
    remaining = 100 - percentage
    
    # Colors matching the user's provided UI
    color_progress = '#149B8D' # A teal/green color
    color_remaining = '#D3D3D3' # Light gray
    
    # Data to plot
    sizes = [percentage, remaining]
    colors = [color_progress, color_remaining]
    
    # Check if empty (e.g. 0%)
    if percentage == 0:
        sizes = [1, 99] # Just so the chart draws a circle of gray
        colors = [color_remaining, color_remaining]
        
    # Check if full (100%)
    if percentage == 100:
        sizes = [100, 0]
        colors = [color_progress, color_progress]
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(2.5, 2.5), dpi=150) # Smaller high-res image
    
    # Plot the pie chart
    wedges, _ = ax.pie(sizes, colors=colors, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2))
    
    # Add the text in the middle
    ax.text(0, 0.1, f"{percentage}%", ha='center', va='center', fontsize=22, fontweight='bold', color='black')
    ax.text(0, -0.25, "Porcentaje UE", ha='center', va='center', fontsize=9, fontweight='bold', color='black')
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')  
    
    # Save the chart transparently
    plt.tight_layout()
    plt.savefig(output_path, transparent=True, bbox_inches='tight', pad_inches=0.1)
    
    # Close figure to free memory
    plt.close(fig)
    
    return output_path

if __name__ == "__main__":
    # Test generation
    create_percentage_donut(85, "test_donut.png")
    print("Donut generated.")
