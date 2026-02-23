import streamlit as st
from src.db_connection import get_supabase_client

def render_mentor_ie_dashboard():
    user = st.session_state.get('user', {})
    st.title("👨‍🏫 Panel del Mentor Académico (IE)")
    st.write(f"**Bienvenido/a {user.get('nombre_completo', '')}**")
    
    # Logout in sidebar since app.py handles role routing
    st.sidebar.markdown("### Opciones")
    if st.sidebar.button("⏏️ Cerrar Sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()
        
    supabase = get_supabase_client()
    
    # 1. Fetch Students assigned to this Mentor IE
    res_students = supabase.table("proyectos_dual").select(
        "id, nombre_proyecto, calificacion_ie, alumnos(id, matricula, nombre, ap_paterno)"
    ).eq("mentor_ie_id", user["id"]).execute()
    
    if not res_students.data:
        st.info("Actualmente no tienes estudiantes DUAL asignados.")
        return
        
    projects = res_students.data
    st.subheader(f"Tus Estudiantes Asignados ({len(projects)})")
    
    # Display each student in an expander
    for proj in projects:
        alumno = proj.get("alumnos", {})
        nombre_completo = f"{alumno.get('nombre', '')} {alumno.get('ap_paterno', '')}"
        matricula = alumno.get('matricula', 'S/N')
        global_ie_calif = proj.get("calificacion_ie")
        
        status_text = f"✅ Evaluación Guardada ({global_ie_calif:.2f}/10)" if global_ie_calif is not None else "⚠️ Pendiente de Evaluación"
        
        with st.expander(f"🎓 {nombre_completo} - {matricula} | {status_text}"):
            st.write(f"**Proyecto:** {proj.get('nombre_proyecto')}")
            
            # Fetch subjects for this student
            res_subs = supabase.table("inscripciones_asignaturas").select(
                "id, calificacion_ie_materia, descripcion_actividades, asignaturas(nombre, clave_asignatura)"
            ).eq("alumno_id", alumno.get("id")).execute()
            
            subs = res_subs.data if res_subs.data else []
            if not subs:
                st.warning("El alumno no tiene materias registradas en su carga académica DUAL.")
                continue
                
            st.markdown("---")
            st.write("#### Evaluación por Materia (30% Institucional)")
            st.write("Como Mentor Institucional (Maestro), debes evaluar del 0 al 10 el desempeño que tuvo el estudiante dentro de la empresa o proyecto, ponderando **cómo aplicó los conocimientos de cada materia en específico**.")
            
            # Form to save grades
            with st.form(f"form_eval_ie_{proj['id']}"):
                grades = {}
                for s in subs:
                    mat_name = s.get("asignaturas", {}).get("nombre", "Materia")
                    actividades = s.get("descripcion_actividades") or "Sin descripción registrada por el alumno."
                    current_grade = s.get("calificacion_ie_materia")
                    
                    st.markdown(f"##### 📚 Materia: {mat_name}")
                    st.info(f"**Actividades Planeadas:** {actividades}")
                    
                    # Number input
                    grade_input = st.number_input(
                        f"Ingresar Calificación (0 - 10)", 
                        min_value=0.0, 
                        max_value=10.0, 
                        value=float(current_grade) if current_grade is not None else 0.0, 
                        step=0.1,
                        key=f"gr_{s['id']}"
                    )
                    grades[s["id"]] = grade_input
                    st.divider()
                
                sum_grades = sum(grades.values())
                avg_grade = sum_grades / len(subs) if subs else 0.0
                st.success(f"**Promedio Calculado:** {avg_grade:.2f}/10. Esta calificación será enviada a Coordinación y representará automáticamente el 30% Institucional.")
                
                submitted = st.form_submit_button("Guardar Calificaciones del Estudiante", type="primary")
                if submitted:
                    with st.spinner("Guardando en base de datos..."):
                        all_success = True
                        for sub_id, grade in grades.items():
                            res = supabase.table("inscripciones_asignaturas").update({
                                "calificacion_ie_materia": grade
                            }).eq("id", sub_id).execute()
                            if not res.data:
                                all_success = False
                                
                        # Also save the overall avg in proyectos_dual
                        supabase.table("proyectos_dual").update({
                            "calificacion_ie": avg_grade
                        }).eq("id", proj["id"]).execute()
                        
                        if all_success:
                            st.success("Evaluaciones publicadas exitosamente.")
                            st.rerun()
                        else:
                            st.error("Ocurrió un error guardando las calificaciones.")
