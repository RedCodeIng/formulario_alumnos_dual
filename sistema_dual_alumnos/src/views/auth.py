import streamlit as st
import time
from src.db_connection import get_supabase_client
from src.components.login_ui import get_login_css, get_login_header

def render_login():
    """Renders the login view for Students."""
    st.markdown(get_login_css(), unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(get_login_header(), unsafe_allow_html=True)
        
        with st.form("login_form"):
            matricula = st.text_input("Matrícula")
            curp = st.text_input("CURP", type="password")
            
            # Fetch Carreras from DB
            supabase = get_supabase_client()
            carreras_options = {}
            try:
                 res_carreras = supabase.table("carreras").select("id, nombre").execute()
                 if res_carreras.data:
                     carreras_data = res_carreras.data
                     carreras_data.sort(key=lambda x: x["nombre"])
                     carreras_options = {c["nombre"]: c["id"] for c in carreras_data}
            except Exception as e:
                 st.error(f"Error cargando carreras: {e}")
            
            selected_career_name = None
            selected_career_id = None

            if carreras_options:
                selected_career_name = st.selectbox("Seleccione su Carrera / División", list(carreras_options.keys()))
                if selected_career_name:
                    selected_career_id = carreras_options[selected_career_name]
            else:
                st.error("No se pudieron cargar las carreras. Verifique la conexión a base de datos.")

            submitted = st.form_submit_button("Ingresar")
            
            if submitted:
                if not matricula or not curp:
                    st.error("Por favor, ingrese Matrícula y CURP.")
                elif not selected_career_id:
                     st.error("Seleccione su carrera.")
                else:
                    try:
                        # 1. Check if student exists
                        res = supabase.table("alumnos").select("*").eq("matricula", matricula).execute()
                        
                        if res.data:
                            student = res.data[0]
                            # 2. Check Password (CURP)
                            if student.get("curp") == curp:
                                st.session_state["authenticated"] = True
                                st.session_state["user"] = student
                                st.session_state["role"] = "student"
                                st.session_state["selected_career"] = selected_career_name
                                st.session_state["selected_career_id"] = selected_career_id
                                st.success(f"Bienvenido al Portal DUAL - {selected_career_name}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("CURP incorrecta.")
                        else:
                            # 3. Whitelist Check
                            # Check if matricula is in lista_blanca
                            res_wb = supabase.table("lista_blanca").select("*").eq("matricula", matricula).execute()
                            
                            if res_wb.data:
                                wb_entry = res_wb.data[0]
                                wb_curp = wb_entry.get("curp")
                                wb_name = wb_entry.get("nombre_completo", "")
                                
                                # Validate CURP (Strict check against whitelist)
                                # User input 'curp' is the password field here
                                if wb_curp and curp.strip().upper() != wb_curp.strip().upper():
                                     st.error("La CURP ingresada no coincide con el registro autorizado.")
                                else:
                                    # SPLIT NAME LOGIC (Basic)
                                    parts = wb_name.split()
                                    npm = ""
                                    npp = ""
                                    nname = ""
                                    
                                    if len(parts) >= 3:
                                        npm = parts[-1]
                                        npp = parts[-2]
                                        nname = " ".join(parts[:-2])
                                    elif len(parts) == 2:
                                        npp = parts[-1]
                                        nname = parts[0]
                                    else:
                                        nname = wb_name
                                        
                                    st.session_state["registro_step"] = 1
                                    st.session_state["user"] = {
                                        "matricula": matricula, 
                                        "curp": curp,
                                        "nombre": nname,
                                        "ap_paterno": npp,
                                        "ap_materno": npm
                                    }
                                    st.session_state["authenticated"] = False
                                    st.session_state["showing_registro"] = True
                                    st.session_state["role"] = "student_register"
                                    st.session_state["selected_career"] = selected_career_name
                                    st.session_state["selected_career_id"] = selected_career_id
                                    
                                    st.success(f"Matrícula autorizada. Bienvenido(a) {nname}.")
                                    time.sleep(1.5)
                                    st.rerun()
                            else:
                                st.error("Matrícula no autorizada. Contacte a su coordinador para ser dado de alta en la lista blanca.")
                                st.info("Si es un error, verifique que su matrícula esté escrita correctamente.")

                    except Exception as e:
                         st.error(f"Error en autenticación: {e}")
