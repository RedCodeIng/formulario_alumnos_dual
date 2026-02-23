import streamlit as st
from src.components.cards import get_card_html
from src.db_connection import get_supabase_client
import pandas as pd
import re

def render_dashboard():
    st.title("Panel de Control - Alumno DUAL")
    st.markdown("---")
    
    user = st.session_state.get("user", {})
    estatus = user.get("estatus", "No definido")
    
    # KPI Cards Row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(get_card_html("Estatus DUAL", estatus, "fas fa-info-circle"), unsafe_allow_html=True)
    with col2:
        st.markdown(get_card_html("Semestre", user.get("semestre", "N/A"), "fas fa-calendar", color="#a48857"), unsafe_allow_html=True)
    with col3:
         # Project info fetch
         supabase = get_supabase_client()
         res_p = supabase.table("proyectos_dual").select("nombre_proyecto").eq("alumno_id", user.get("id")).execute()
         p_name = res_p.data[0]["nombre_proyecto"] if res_p.data else "Sin Proyecto"
         st.markdown(get_card_html("Proyecto Activo", p_name[:20] + "..." if len(p_name)>20 else p_name, "fas fa-project-diagram"), unsafe_allow_html=True)
         

    st.markdown("---")
    
    # Tabs for student
    tab_docs, tab_academic, tab_profile = st.tabs(["Mis Documentos", "Carga Académica", "Mi Perfil"])
    
    with tab_docs:
        # Placeholder for documents
        st.header("Documentación DUAL")
        st.info("Aquí podrás descargar y subir tus formatos (Anexo 5.1, Carta de Asignación, Reportes Bimestrales).")
        # File uploader demo
        
        uploaded_file = st.file_uploader("Subir Reporte Bimestral (PDF)")
        if uploaded_file is not None:
             st.success("Archivo subido correctamente (Simulación).")
             
    with tab_academic:
        st.header("Carga Académica")
        
        student_id = user.get("id")
        selected_career_id = user.get("carrera_id")
        
        # 1. Fetch CURRENT Subjects
        st.markdown("### Materias Inscritas Actuales")
        try:
            res_insc = supabase.table("inscripciones_asignaturas").select(
                "id, grupo, asignaturas(clave_asignatura, nombre, semestre), maestros(nombre_completo)"
            ).eq("alumno_id", student_id).execute()
            
            if res_insc.data:
                data_rows = []
                for item in res_insc.data:
                    asign = item.get('asignaturas', {})
                    docente = item.get('maestros', {})
                    data_rows.append({
                        "id_inscripcion": item['id'],
                        "Clave": asign.get('clave_asignatura'),
                        "Asignatura": asign.get('nombre'),
                        "Semestre": asign.get('semestre'),
                        "Grupo": item.get('grupo'),
                        "Docente": docente.get('nombre_completo', 'Sin Asignar')
                    })
                
                # Display current subjects with delete option
                for row in data_rows:
                    col_info, col_del = st.columns([5, 1])
                    col_info.write(f"**{row['Asignatura']}** ({row['Clave']}) - Gpo: {row['Grupo']} | *{row['Docente']}*")
                    if col_del.button("❌ Eliminar", key=f"del_subj_{row['id_inscripcion']}"):
                         try:
                             supabase.table("inscripciones_asignaturas").delete().eq("id", row['id_inscripcion']).execute()
                             st.success("Materia eliminada.")
                             st.rerun()
                         except Exception as e:
                             st.error(f"Error al eliminar materia: {e}")
                    st.divider()

            else:
                st.info("No hay asignaturas inscritas actualmente.")
        except Exception as e:
            st.error(f"Error al cargar carga académica: {e}")
            
        st.markdown("---")
        st.markdown("### Agregar Nueva Asignatura")
        
        # 2. Re-use Registro Logic for Adding Subjects
        c_filter1, c_filter2 = st.columns(2)
        with c_filter1:
            st.write(f"**Carrera:** {user.get('carrera', 'N/A')}")
        with c_filter2:
            sem_options = ["Todos", "6", "7", "8", "9"]
            current_sem = user.get("semestre", "6")
            default_index = sem_options.index(current_sem) if current_sem in sem_options else 0
            selected_sem_filter = st.selectbox("Filtrar Materias por Semestre", sem_options, index=default_index, key="add_subj_sem")

        query = supabase.table("asignaturas").select("id, nombre, clave_asignatura, semestre")
        if selected_career_id:
             query = query.eq("carrera_id", selected_career_id)
        if selected_sem_filter != "Todos":
            query = query.eq("semestre", selected_sem_filter)

        res_subjects = query.execute()
        subjects = res_subjects.data if res_subjects.data else []
        subject_options = {f"{s['clave_asignatura']} - {s['nombre']} (Sem {s['semestre']})": s["id"] for s in subjects}

        with st.form("add_subject_form"):
            c1, c2 = st.columns(2)
            with c1:
                sel_subj_name = st.selectbox("Asignatura", list(subject_options.keys()) if subjects else ["No hay asignaturas"])
                subject_id = subject_options.get(sel_subj_name)
                grupo = st.text_input("Grupo (Ej. 8101)")
                
            with c2:
                filtered_teachers = []
                if subject_id:
                    res_rels = supabase.table("rel_maestros_asignaturas").select("maestro_id").eq("asignatura_id", subject_id).execute()
                    teacher_ids = [r["maestro_id"] for r in res_rels.data] if res_rels.data else []
                    
                    if teacher_ids:
                        res_teachers = supabase.table("maestros").select("id, clave_maestro, nombre_completo").in_("id", teacher_ids).execute()
                        filtered_teachers = res_teachers.data if res_teachers.data else []
                
                if filtered_teachers:
                    cleaned_options = {}
                    for t in filtered_teachers:
                        raw_name = t['nombre_completo']
                        clean_name = re.sub(r'\s*\([^)]*\)', '', raw_name).strip()
                        display_str = f"{t['clave_maestro']} - {clean_name}"
                        cleaned_options[display_str] = t["id"]
                    teacher_options = cleaned_options
                else:
                     teacher_options = {}

                sel_teacher_name = st.selectbox(
                    "Maestro (Docente)", 
                    list(teacher_options.keys()) if teacher_options else ["No hay maestros asignados a esta materia"]
                )
                
                st.write("Parciales a Cursar:")
                col_chk1, col_chk2, col_chk3 = st.columns(3)
                with col_chk1: p1 = st.checkbox("Parcial 1", value=True)
                with col_chk2: p2 = st.checkbox("Parcial 2", value=True)
                with col_chk3: p3 = st.checkbox("Parcial 3", value=True)

            submitted_add = st.form_submit_button("Agregar Materia")
            if submitted_add:
                 if not grupo:
                      st.error("Ingrese el grupo.")
                 elif not sel_teacher_name or sel_teacher_name == "No hay maestros asignados a esta materia":
                      st.error("Seleccione un maestro válido.")
                 else:
                      try:
                          # Check if already enrolled
                          check_res = supabase.table("inscripciones_asignaturas").select("id").eq("alumno_id", student_id).eq("asignatura_id", subject_id).execute()
                          if (check_res.data):
                               st.error("Ya está inscrito en esta materia.")
                          else:
                               supabase.table("inscripciones_asignaturas").insert({
                                   "alumno_id": student_id,
                                   "asignatura_id": subject_id,
                                   "maestro_id": teacher_options[sel_teacher_name],
                                   "grupo": grupo,
                                   "parcial_1": p1,
                                   "parcial_2": p2,
                                   "parcial_3": p3
                               }).execute()
                               st.success("Materia inscrita exitosamente.")
                               st.rerun()
                      except Exception as e:
                          st.error(f"Error al inscribir materia: {e}")

    with tab_profile:
        st.header("Mi Perfil")
        # Show read-only profile info
        c1, c2 = st.columns(2)
        c1.text_input("Nombre Completo", value=f"{user.get('nombre')} {user.get('ap_paterno')} {user.get('ap_materno')}", disabled=True)
        c2.text_input("Matrícula", value=user.get("matricula"), disabled=True)
        c1.text_input("Correo Institucional", value=user.get("email_institucional"), disabled=True)
        c2.text_input("Carrera", value=user.get("carrera"), disabled=True)
