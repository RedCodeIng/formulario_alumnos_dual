import streamlit as st
import pandas as pd
from src.db_connection import get_supabase_client

def render_student_dashboard():
    st.title("Mi Portal DUAL")
    
    user = st.session_state.get("user", {})
    if not user:
        st.error("Sesión no válida.")
        return

    supabase = get_supabase_client()
    
    # FETCH DATA
    # 1. Project
    project = {}
    try:
        res_proj = supabase.table("proyectos_dual").select("*, unidades_economicas(nombre_comercial), mentores_ue(nombre_completo)").eq("alumno_id", user.get("id")).execute()
        if res_proj.data:
            project = res_proj.data[0]
            # Flatten for easier access if needed, or just use keys
    except Exception as e:
        st.error(f"Error cargando proyecto: {e}")

    # 2. Subjects
    subjects = []
    try:
        # Note: Supabase join syntax might vary depending on client version/setup.
        # Simple approach: fetch IDs and then fetch details if nested select is tricky without ORM
        # But let's try standard PostgREST syntax: select(*, asignaturas(*), maestros(*))
        res_subs = supabase.table("inscripciones_asignaturas").select(
            "*, asignaturas(nombre, clave_asignatura), maestros(nombre_completo)"
        ).eq("alumno_id", user.get("id")).execute()
        
        if res_subs.data:
            subjects = res_subs.data
    except Exception as e:
        st.error(f"Error cargando materias: {e}")

    # Success Box for New Registrations
    if st.session_state.get("registro_complete"):
        st.success("¡Tu registro ha sido completado exitosamente! Ahora puedes ver tu información y estatus.")
        # Optional: Clear the flag so it doesn't show on every refresh, 
        # but for now let's keep it until they logout or for this session.
    
    # UI LAYOUT
    st.markdown(f"### Bienvenido, {user.get('nombre')} {user.get('ap_paterno')}")
    
    tab1, tab2 = st.tabs(["Mi Información", "Mi Proyecto"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Datos Personales")
            st.write(f"**Matrícula:** {user.get('matricula')}")
            st.write(f"**CURP:** {user.get('curp')}")
            st.write(f"**Email Institucional:** {user.get('email_institucional')}")
            st.write(f"**Teléfono:** {user.get('telefono', 'No registrado')}")
            
        with col2:
            st.markdown("#### Datos Académicos")
            # Robust Career Display
            career_name = st.session_state.get('selected_career') or user.get('carrera') or "Cargando..."
            st.write(f"**Carrera:** {career_name}") 
            st.write(f"**Semestre:** {user.get('semestre')}")
            st.write(f"**Estatus:** {user.get('estatus')}")

        st.markdown("---")
        st.subheader("Carga Académica Actual")
        
        if subjects:
            # Prepare DataFrame for display
            data_rows = []
            for s in subjects:
                asig = s.get("asignaturas", {})
                maestro = s.get("maestros", {})
                data_rows.append({
                    "Clave": asig.get("clave_asignatura", "N/A"),
                    "Asignatura": asig.get("nombre", "N/A"),
                    "Maestro": maestro.get("nombre_completo", "N/A"),
                    "Grupo": s.get("grupo", "N/A"),
                    "P1": "✅" if s.get("parcial_1") else "❌",
                    "P2": "✅" if s.get("parcial_2") else "❌",
                    "P3": "✅" if s.get("parcial_3") else "❌",
                })
            
            st.dataframe(pd.DataFrame(data_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No tienes asignaturas registradas.")

    with tab2:
        if project:
            st.subheader(f"Proyecto: {project.get('nombre_proyecto')}")
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                ue = project.get("unidades_economicas", {})
                mentor = project.get("mentores_ue", {})
                st.write(f"**Empresa:** {ue.get('nombre_comercial', 'N/A')}")
                st.write(f"**Mentor Industrial:** {mentor.get('nombre_completo', 'N/A')}")
            
            with c_p2:
                st.write(f"**Fecha Inicio:** {project.get('fecha_inicio_convenio')}")
                st.write(f"**Fecha Fin:** {project.get('fecha_fin_convenio')}")
            
            st.markdown("#### Descripción del Proyecto")
            st.info(project.get("descripcion_proyecto", "Sin descripción detallada."))
            
        else:
            st.warning("No tienes un proyecto registrado aún.")
