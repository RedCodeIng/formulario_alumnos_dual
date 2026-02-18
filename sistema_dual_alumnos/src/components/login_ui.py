
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
            padding: 2.5rem;
            border-radius: 8px; /* Slightly sharper corners */
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1); /* Deeper shadow */
            width: 100%;
            max-width: 450px;
            text-align: center;
            border-top: 6px solid var(--primary); /* Use global variable */
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
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin-bottom: 25px;
            width: 100%;
        }
        .logo-img-login {
            height: 55px; /* TESE and EdoMex slightly smaller */
            width: auto;
            object-fit: contain;
        }
        .logo-img-dual {
            height: 90px; /* Dual Logo larger and central */
            width: auto;
            object-fit: contain;
        }
    </style>
    """

def get_login_header():
    # Paths
    base_path = "src/assets/images/logos"
    
    # Load Real Images
    # We need to construct absolute path or relative from cwd
    # Assuming CWD is project root
    logo_tese = load_image_as_base64(os.path.join(base_path, "logo_institucional_tese.png"))
    logo_edomex = load_image_as_base64(os.path.join(base_path, "logo_estado_mexico.png"))
    logo_dual = load_image_as_base64(os.path.join(base_path, "logo_dual_sistema.png"))
    
    img_tese = f'<img src="{logo_tese}" class="logo-img-login">' if logo_tese else ''
    img_edomex = f'<img src="{logo_edomex}" class="logo-img-login">' if logo_edomex else ''
    img_dual = f'<img src="{logo_dual}" class="logo-img-dual">' if logo_dual else ''

    return f"""
    <div class="login-card">
        <div class="logo-row">
            {img_tese}
            {img_dual}
            {img_edomex}
        </div>
        <div class="login-header">Portal de Alumnos DUAL</div>
        <div class="login-subtext">Gobierno del Estado de México</div>
    </div>
    """
