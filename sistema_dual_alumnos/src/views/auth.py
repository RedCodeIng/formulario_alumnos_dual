import streamlit as st
import time
import hashlib
from src.db_connection import get_supabase_client
from src.components.login_ui import get_login_css, get_login_header

def render_login():
    """Renders the login view for Students and Mentors UE."""
    st.markdown(get_login_css(), unsafe_allow_html=True)
    
    # --- Data Fetching (Outside Form) ---
    carreras_options = {}
    fetch_error = None
    
    try:
        supabase = get_supabase_client()
        res_carreras = supabase.table("carreras").select("id, nombre").execute()
        if res_carreras.data:
            carreras_data = res_carreras.data
            carreras_data.sort(key=lambda x: x["nombre"])
            carreras_options = {c["nombre"]: c["id"] for c in carreras_data}
    except Exception as e:
        fetch_error = f"Error conectando a la base de datos: {e}"
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown(get_login_header(), unsafe_allow_html=True)
        
        if fetch_error:
             st.error(fetch_error)
        
        tab_student, tab_mentor, tab_mentor_ie = st.tabs(["🎓 Acceso Alumnos", "🏢 Acceso Mentores UE", "👨‍🏫 Acceso Mentores IE"])
        
        with tab_student:
        
            with st.form("login_form"):
                matricula = st.text_input("Matrícula")
                curp = st.text_input("CURP", type="password")
            
                selected_career_name = None
                selected_career_id = None

                if carreras_options:
                    selected_career_name = st.selectbox("Seleccione su Carrera / División", list(carreras_options.keys()))
                    if selected_career_name:
                        selected_career_id = carreras_options[selected_career_name]
                elif not fetch_error:
                    st.warning("No se pudieron cargar las carreras. Verifique la conexión a base de datos.")

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
                                    # 2.1 Enforce Career Match (Fix Loophole)
                                    student_career_id = student.get("carrera_id")
                                    if student_career_id and student_career_id != selected_career_id:
                                        st.error("Usted está registrado en otra carrera. Por favor seleccione la carrera correcta en el menú.")
                                    else:
                                        from src.utils.db_actions import get_active_period_id
                                        periodo_id = get_active_period_id()
                                        
                                        # Check if student has academic load for the current period
                                        needs_reenrollment = False
                                        if periodo_id:
                                            res_insc = supabase.table("inscripciones_asignaturas").select("id").eq("alumno_id", student["id"]).eq("periodo_id", periodo_id).execute()
                                            if not res_insc.data:
                                                needs_reenrollment = True
                                        
                                        if needs_reenrollment:
                                            st.session_state["registro_step"] = 1
                                            st.session_state["user"] = student
                                            st.session_state["authenticated"] = False
                                            st.session_state["showing_registro"] = True
                                            st.session_state["role"] = "student_register"
                                            st.session_state["selected_career"] = selected_career_name
                                            st.session_state["selected_career_id"] = selected_career_id
                                            
                                            st.info(f"Hola {student.get('nombre', '')}, detectamos que necesitas realizar tu carga académica para el periodo actual.")
                                            time.sleep(1.5)
                                            st.rerun()
                                        else:
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
                                # Check if matricula is in lista_blanca AND matches selected career
                                try:
                                    res_wb = supabase.table("lista_blanca").select("*").eq("matricula", matricula).eq("carrera_id", selected_career_id).execute()
                                
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
                                        
                                            st.success(f"Matrícula autorizada para {selected_career_name}. Bienvenido(a) {nname}.")
                                            time.sleep(1.5)
                                            st.rerun()
                                    else:
                                        # Check if it exists for ANOTHER career to give better error?
                                        # Or just generic error to avoid leaking info.
                                        # Generic is safer, but user asked for restriction.
                                        st.error("Matrícula no autorizada para la carrera seleccionada.")
                                        st.info("Verifique que seleccionó la carrera correcta o contacte a su coordinador.")
                                except Exception as e:
                                    st.error(f"Error consultando lista blanca: {e}")
                        except Exception as e:
                            st.error(f"Error general en login: {e}")

        with tab_mentor:
            st.markdown("### Portal Empresarial")
            st.info("Utilice el correo y contraseña proporcionados por el Coordinador DUAL.")
            
            with st.form("login_mentor_form"):
                email = st.text_input("Correo Electrónico (Empresarial)")
                password = st.text_input("Contraseña", type="password")
                
                submitted_mentor = st.form_submit_button("Ingresar como Mentor")
                
                if submitted_mentor:
                    if not email or not password:
                        st.error("Por favor, ingrese Correo y Contraseña.")
                    else:
                        try:
                            # Search by email
                            res_mentor = supabase.table("mentores_ue").select("*").eq("email", email).execute()
                            if res_mentor.data:
                                mentor = res_mentor.data[0]
                                
                                # Hash input password
                                hashed_input = hashlib.sha256(password.encode('utf-8')).hexdigest()
                                stored_hash = mentor.get("password_hash")
                                
                                if not stored_hash:
                                    st.error("Esta cuenta no tiene contraseña configurada. Contacte al coordinador.")
                                elif stored_hash == hashed_input:
                                    if mentor.get("is_active") == False:
                                        st.error("Su cuenta está inactiva. Contacte al coordinador DUAL para reactivarla.")
                                    else:
                                        st.session_state["authenticated"] = True
                                        st.session_state["user"] = mentor
                                        st.session_state["role"] = "mentor_ue"
                                        
                                        # Get company name
                                        res_ue = supabase.table("unidades_economicas").select("nombre_comercial").eq("id", mentor.get("ue_id")).execute()
                                        if res_ue.data:
                                             st.session_state["ue_name"] = res_ue.data[0]["nombre_comercial"]
                                             
                                        st.success(f"Bienvenido(a) {mentor['nombre_completo']}")
                                        time.sleep(1)
                                        st.rerun()
                                else:
                                    st.error("Contraseña incorrecta.")
                            else:
                                st.error("Correo electrónico no encontrado en el sistema empresarial.")
                        except Exception as e:
                            st.error(f"Error de conexión en login: {e}")

        with tab_mentor_ie:
            st.markdown("### Portal Académico IE")
            st.info("Utilice su correo institucional y la contraseña proporcionada.")
            
            with st.form("login_mentor_ie_form"):
                email_ie = st.text_input("Correo Institucional")
                pass_ie = st.text_input("Contraseña", type="password")
                
                submitted_ie = st.form_submit_button("Ingresar como Mentor IE")
                
                if submitted_ie:
                    if not email_ie or not pass_ie:
                        st.error("Por favor, ingrese Correo y Contraseña.")
                    else:
                        try:
                            res_ie = supabase.table("maestros").select("*").eq("email_institucional", email_ie).eq("es_mentor_ie", True).execute()
                            if res_ie.data:
                                mentor_ie = res_ie.data[0]
                                hashed_input = hashlib.sha256(pass_ie.encode('utf-8')).hexdigest()
                                stored_hash = mentor_ie.get("password_hash")
                                
                                if not stored_hash:
                                    st.error("Esta cuenta no tiene contraseña configurada. Contacte al coordinador.")
                                elif stored_hash == hashed_input:
                                    st.session_state["authenticated"] = True
                                    st.session_state["user"] = mentor_ie
                                    st.session_state["role"] = "mentor_ie"
                                    st.success(f"Bienvenido(a) Profesor(a) {mentor_ie['nombre_completo']}")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Contraseña incorrecta.")
                            else:
                                st.error("Tus credenciales no existen o no tienes el rol de Mentor IE asignado.")
                        except Exception as e:
                            st.error(f"Error de conexión en login: {e}")
