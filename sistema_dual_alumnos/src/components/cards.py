def get_card_html(title, value, icon, color="#8d2840"):
    return f"""
    <div style="
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid {color};
        margin-bottom: 20px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin: 0; color: #6c757d; font-size: 14px; text-transform: uppercase;">{title}</h4>
                <h2 style="margin: 10px 0 0 0; color: {color}; font-size: 28px; font-weight: bold;">{value}</h2>
            </div>
            <div style="font-size: 32px; color: {color}; opacity: 0.2;">
                <i class="{icon}"></i>
            </div>
        </div>
    </div>
    """
