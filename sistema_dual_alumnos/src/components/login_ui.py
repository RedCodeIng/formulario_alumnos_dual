
import os
import base64

def load_image_as_base64(path):
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except:
        return ""

def get_login_css():
    return """
    <style>
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
            padding: 20px;
        }
        .login-card {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 8px; /* Slightly sharper corners */
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1); /* Deeper shadow */
            width: 100%;
            box-sizing: border-box;
            text-align: center;
            border-top: 6px solid var(--primary); /* Use global variable */
            margin-bottom: 1rem;
        }
        .login-header {
            color: var(--primary) !important;
            margin-bottom: 0.5rem;
            font-size: 24px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .login-subtext {
            color: var(--secondary) !important;
            margin-bottom: 1.5rem;
            font-size: 14px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .logo-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            width: 100%;
            padding: 0;
            box-sizing: border-box;
        }
        .logo-img-login {
            height: auto;
            max-height: 65px; /* TESE and EdoMex maximum size */
            max-width: 48%; /* Ensure they don't overflow the container */
            object-fit: contain;
        }
        
        /* Mobile Responsiveness for Logos */
        @media (max-width: 400px) {
            .logo-img-login {
                max-height: 50px;
            }
            .logo-row {
                gap: 10px;
            }
        }
    </style>
    """

def get_login_header():
    # Paths - Use absolute path relative to this file to be safe
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level from 'components' to 'src', then to 'assets/images/logos'
    # Structure: src/components/login_ui.py -> src/assets
    base_path = os.path.join(os.path.dirname(current_dir), "assets", "images", "logos")
    
    # Load Real Images
    logo_tese = load_image_as_base64(os.path.join(base_path, "logo_institucional_tese.png"))
    logo_edomex = load_image_as_base64(os.path.join(base_path, "logo_estado_mexico.png"))
    
    img_tese = f'<img src="{logo_tese}" class="logo-img-login">' if logo_tese else ''
    img_edomex = f'<img src="{logo_edomex}" class="logo-img-login">' if logo_edomex else ''

    return f"""
    <div class="login-card">
        <div class="logo-row">
            {img_tese}
            {img_edomex}
        </div>
        <div class="login-header">Portal de Alumnos DUAL</div>
        <div class="login-subtext">Gobierno del Estado de México</div>
    </div>
    """
