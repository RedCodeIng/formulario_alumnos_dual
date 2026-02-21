import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
from src.db_connection import get_supabase_client
from src.utils.doc_generator import generar_documento_word

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
        res_proj = supabase.table("proyectos_dual").select("*, unidades_economicas(*), mentores_ue(*), maestros(*)").eq("alumno_id", user.get("id")).execute()
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
    
    tab1, tab2, tab3 = st.tabs(["Mi Información", "Mi Proyecto", "📁 Mis Documentos"])
    
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

    with tab3:
        st.subheader("Documentos Oficiales DUAL")
        st.write("Desde aquí puedes descargar en formato Word las plantillas de tus documentos oficiales generados con tu información actual. Estos documentos se generan al momento y no se guardan permanentently en el sistema base.")
        
        if not project:
            st.warning("Necesitas tener un Proyecto DUAL registrado y activo para generar documentos.")
        else:
            # Validations similar to Coordinator
            has_project_and_ue = bool(project.get("ue_id") and project.get("mentor_ue_id"))
            has_mentor_ie = bool(project.get("mentor_ie_id"))
            has_all_reqs = has_project_and_ue and has_mentor_ie

            # Prepare data context for the documents
            ue = project.get("unidades_economicas", {}) or {}
            mentor_ue = project.get("mentores_ue", {}) or {}
            mentor_ie = project.get("maestros", {}) or {}
            
            # Basic context map (matches what doc_generator expects)
            context = {
                "alumno_nombre": f"{user.get('nombre')} {user.get('ap_paterno')} {user.get('ap_materno', '')}".strip(),
                "alumno_matricula": user.get('matricula'),
                "alumno_carrera": st.session_state.get('selected_career') or user.get('carrera', 'N/A'),
                "alumno_semestre": str(user.get('semestre', 'N/A')),
                "empresa_nombre": ue.get('nombre_comercial', 'N/A'),
                "empresa_rfc": ue.get('rfc', 'N/A'),
                "empresa_direccion": ue.get('direccion_fiscal', 'N/A'),
                "empresa_representante": ue.get('nombre_titular', 'N/A'),
                "empresa_cargo_representante": ue.get('cargo_titular', 'N/A'),
                "mentor_ue_nombre": mentor_ue.get('nombre_completo', 'N/A'),
                "mentor_ue_cargo": mentor_ue.get('cargo', 'N/A'),
                "mentor_ue_email": mentor_ue.get('email', 'N/A'),
                "mentor_ue_telefono": mentor_ue.get('telefono', 'N/A'),
                "mentor_ie_nombre": mentor_ie.get('nombre_completo', 'N/A'),
                "proyecto_nombre": project.get('nombre_proyecto'),
                "proyecto_fecha_inicio": str(project.get('fecha_inicio_convenio')),
                "proyecto_fecha_fin": str(project.get('fecha_fin_convenio')),
                "materia_nombre": "Asignaturas Modelo DUAL",
                "calificacion": "100", # Demostrativo
                "fecha_actual": datetime.now().strftime('%d/%m/%Y')
            }
            
            # Format subjects for Anexo 5.1
            materias_fmt = []
            for s in subjects:
                asig = s.get("asignaturas", {})
                maestro = s.get("maestros", {})
                materias_fmt.append({
                    "nombre": asig.get("nombre", "N/A"),
                    "semestre": str(asig.get("semestre", "N/A")),
                    "maestro": maestro.get("nombre_completo", "Sin Asignar")
                })
            context["materias"] = materias_fmt
            
            # Let's create UI cards for downloading
            c_doc1, c_doc2 = st.columns(2)
            
            with c_doc1:
                st.markdown("##### 📄 Anexo 5.1: Plan de Formación Especialidad")
                st.write("Contiene el acuerdo inicial, tus datos, los de la empresa y la lista de materias involucradas.")
                
                if not has_project_and_ue:
                    st.error("🛑 Aún no tienes la información completa (Empresa/Mentor UE) para poder descargar este Anexo.")
                    st.button("Generar Anexo 5.1", disabled=True, key="btn_gen_51_disabled")
                else:
                    st.success("✅ Este anexo ya es posible descargarlo.")
                    if st.button("Generar Anexo 5.1", key="btn_gen_51"):
                        with st.spinner("Generando documento..."):
                            # Get the parent folder for both apps (SISTEMA DUAL FINAL)
                            base_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                            template_path = os.path.join(base_project_dir, "sistema_dual", "src", "templates", "docs", "Anexo_5.1_Plan_de_Formacion.docx")
                            if os.path.exists(template_path):
                                # Temporary file
                                fd, temp_path = tempfile.mkstemp(suffix=".docx")
                                os.close(fd)
                                
                                success, msg = generar_documento_word(template_path, temp_path, context)
                                
                                if success:
                                    st.success("Documento generado exitosamente.")
                                    with open(temp_path, "rb") as f:
                                        st.download_button(
                                            label="⬇️ Descargar Anexo 5.1 (.docx)",
                                            data=f,
                                            file_name=f"Anexo_5.1_{user.get('matricula')}.docx",
                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                        )
                                    # Clean up is handled by OS eventually, or we could delete it after, 
                                    # but Streamlit's rerun model makes post-download deletion tricky here.
                                    # Mkstemp in tmp dir is safe enough for temporary flies.
                                else:
                                    st.error(f"Error al generar: {msg}")
                            else:
                                st.error("Plantilla del Anexo 5.1 no encontrada.")

            with c_doc2:
                st.markdown("##### 📄 Anexo 5.4: Reporte de Actividades")
                st.write("Formato oficial para reportar tus actividades (bitácoras) mensuales o semanales.")
                
                if not has_all_reqs:
                    st.error("🛑 Aún no tienes la información completa (Falta Proyecto, Mentor UE o Mentor Institucional Asignado) para poder descargar este Anexo.")
                    st.button("Generar Anexo 5.4", disabled=True, key="btn_gen_54_disabled")
                else:
                    st.success("✅ Este anexo ya es posible descargarlo.")
                    st.caption("Actualmente la generación real del 5.4 requiere las calificaciones tabuladas. Formato base demostrativo.")
                    if st.button("Generar Anexo 5.4", key="btn_gen_54"):
                        with st.spinner("Generando documento..."):
                            base_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                            template_path = os.path.join(base_project_dir, "sistema_dual", "src", "templates", "docs", "Anexo_5.4_Reporte_de_Actividades.docx")
                            if os.path.exists(template_path):
                                fd, temp_path = tempfile.mkstemp(suffix=".docx")
                                os.close(fd)
                                success, msg = generar_documento_word(template_path, temp_path, context)
                                if success:
                                    st.success("Documento generado exitosamente.")
                                    with open(temp_path, "rb") as f:
                                        st.download_button(
                                            label="⬇️ Descargar Anexo 5.4 (.docx)",
                                            data=f,
                                            file_name=f"Anexo_5.4_{user.get('matricula')}.docx",
                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                        )
                                else:
                                    st.error(f"Error al generar: {msg}")
                            else:
                                st.error("Plantilla del Anexo 5.4 no encontrada.")

            c_doc3, c_doc4 = st.columns(2)
            c_doc5, _ = st.columns(2)
            
            # Reusable generic generator block
            def generic_download_card(col, title, desc, reqs, disabled_msg, btn_key, dl_key, filename, template_tgt):
                with col:
                    st.markdown(f"##### {title}")
                    st.write(desc)
                    if not reqs:
                        st.error(disabled_msg)
                        st.button(f"Generar {title.split(':')[0].strip('📄 ')}", disabled=True, key=f"{btn_key}_disabled")
                    else:
                        st.success("✅ Este anexo/documento ya es posible descargarlo.")
                        if st.button(f"Generar {title.split(':')[0].strip('📄✉️📝 ')}", key=btn_key):
                            with st.spinner("Generando documento..."):
                                base_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                                template_path = os.path.join(base_project_dir, "sistema_dual", "src", "templates", "docs", template_tgt)
                                if os.path.exists(template_path):
                                    fd, temp_path = tempfile.mkstemp(suffix=".docx")
                                    os.close(fd)
                                    success, msg = generar_documento_word(template_path, temp_path, context)
                                    if success:
                                        st.success("Documento generado exitosamente.")
                                        with open(temp_path, "rb") as f:
                                            st.download_button(
                                                label=f"⬇️ Descargar {filename}",
                                                data=f,
                                                file_name=f"{filename}_{user.get('matricula')}.docx",
                                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                key=dl_key
                                            )
                                    else: st.error(f"Error: {msg}")
                                else: st.error(f"Plantilla {template_tgt} no encontrada.")

            generic_download_card(
                c_doc3, "📄 Anexo 5.5: Evaluación Final", "Concentrado final y seguimiento global del modelo DUAL.",
                has_all_reqs, "🛑 Requiere tener Mentor IE, Mentor UE y Proyecto Asignados.",
                "btn_gen_55", "dl_btn_55", "Anexo_5.5", "Anexo_5.5_Seguimiento_Modificado.docx"
            )
            
            generic_download_card(
                c_doc4, "✉️ Carta Asignación Mentor IE", "Documento probatorio de asignación institucional con sellos.",
                has_mentor_ie, "🛑 Aún no te han asignado a un Mentor Institucional en el sistema.",
                "btn_gen_carta", "dl_btn_carta", "Carta_Mentor_IE", "Carta_Asignacion_Mentor_IE.docx"
            )
            
            generic_download_card(
                c_doc5, "📝 Acta Calificaciones Materias", "Vaciado simulado de actas de calificaciones de periodo.",
                has_all_reqs, "🛑 Requiere tener modelo activo para vaciar acta.",
                "btn_gen_acta", "dl_btn_acta", "Acta_Calificaciones", "Acta_Calificaciones_Materia.docx"
            )
