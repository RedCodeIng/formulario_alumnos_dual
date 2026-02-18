from src.db_connection import get_supabase_client
from src.utils.db_actions import get_active_period_id

def assign_mentors_round_robin():
    """
    Assigns Academic Mentors (es_mentor_ie=True) to students in the active period
    who do not yet have a mentor assigned. Uses a Round Robin distribution.
    """
    supabase = get_supabase_client()
    period_id = get_active_period_id()
    
    if not period_id:
        return False, "No active period found."

    # 1. Fetch available Mentors
    res_mentors = supabase.table("maestros").select("id").eq("es_mentor_ie", True).execute()
    mentors = [m["id"] for m in res_mentors.data]
    
    if not mentors:
        return False, "No Academic Mentors available for assignment."

    # 2. Fetch Projects without Mentor IE in active period
    # We query projects_dual where mentor_ie_id is null and period_id matches
    res_projects = supabase.table("proyectos_dual").select("id, alumno_id").eq("periodo_id", period_id).is_("mentor_ie_id", "null").execute()
    projects = res_projects.data
    
    if not projects:
        return True, "No pending assignments found."
    
    assigned_count = 0
    mentor_idx = 0
    total_mentors = len(mentors)
    
    # 3. Round Robin Distribution
    for project in projects:
        mentor_id = mentors[mentor_idx]
        
        # Update project with assigned mentor
        supabase.table("proyectos_dual").update({"mentor_ie_id": mentor_id}).eq("id", project["id"]).execute()
        
        assigned_count += 1
        mentor_idx = (mentor_idx + 1) % total_mentors

    return True, f"Successfully assigned mentors to {assigned_count} students."
