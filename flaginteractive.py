# flagpro_shift.py

import uuid
from datetime import datetime, timedelta
from collections import deque, defaultdict
import streamlit as st 

# --- Configuration Constants (Can be moved to st.session_state later) ---
TOTAL_SHIFT_HOURS = 8
ROTATION_CYCLE_DAYS = 28 
SHIFTS_PER_DAY = 3 

# Shift Time definitions (used for display and logic)
SHIFT_TIMES = {
    'Day': (6, 14),
    'Swing': (14, 22),
    'Grave': (22, 6)
}

# --- Data Structures ---

class Worker:
    """Represents a traffic control flagger."""
    def __init__(self, name, certification, source="App Signup"):
        self.worker_id = str(uuid.uuid4())
        self.name = name
        self.is_certified = certification
        self.recruitment_source = source
        self.is_active = True
        self.availability = defaultdict(lambda: True) 

class JobSite:
    """Represents a specific flagging job that needs coverage."""
    def __init__(self, name, location, required_flaggers, start_date, end_date):
        self.job_id = str(uuid.uuid4())
        self.name = name
        self.location = location
        self.required_flaggers = required_flaggers
        self.start_date = start_date
        self.end_date = end_date
        self.assigned_shifts = []

# --- Core Scheduling Logic ---

class AlternatingScheduler:
    """Manages the creation of a balanced, alternating shift loop."""
    # Scheduler now accepts rotation_days as an argument
    def __init__(self, workers, rotation_days=ROTATION_CYCLE_DAYS):
        self.worker_pool = deque(workers)
        self.num_workers = len(workers)
        self.schedule = defaultdict(list) 
        self.rotation_days = rotation_days # Use the user-defined rotation days

    def _generate_shift_pattern(self):
        """Creates a repeating pattern based on shift types and days off."""
        # Simple balanced pattern: 2 Day, 2 Swing, 2 Grave, 2 Off = 8 days cycle
        shift_types = list(SHIFT_TIMES.keys()) * 2 + ['OFF'] * 2 
        # Ensure the pattern repeats enough times to cover the worker pool
        return shift_types * (self.num_workers // len(shift_types) + 1)

    def generate_loop_schedule(self, start_date_str, cycles=1):
        """Generates the main alternating loop for a set number of cycles."""
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        total_days = cycles * self.rotation_days
        shift_pattern = self._generate_shift_pattern()

        st.subheader(f"Generating {total_days}-Day Alternating Loop Schedule")

        for day_offset in range(total_days):
            current_date = start_date + timedelta(days=day_offset)
            date_key = current_date.isoformat()

            # Ensure enough slots are considered (3 shifts)
            required_shifts = len(SHIFT_TIMES) 

            for shift_index in range(required_shifts):
                # The worker assigned rotates daily through the pool
                worker_index = (day_offset + shift_index) % self.num_workers
                assigned_worker = self.worker_pool[worker_index]

                # Determine the shift type based on the rotating pattern index
                pattern_index = (day_offset + shift_index) % len(shift_pattern)
                shift_type = shift_pattern[pattern_index]

                if shift_type != 'OFF':
                    start_h, end_h = SHIFT_TIMES[shift_type]
                    shift_info = {
                        'worker_id': assigned_worker.worker_id,
                        'worker_name': assigned_worker.name,
                        'shift_type': shift_type,
                        'start_time': f"{start_h:02d}:00",
                        'end_time': f"{end_h:02d}:00"
                    }
                    self.schedule[date_key].append(shift_info)

            # Rotate the worker pool once per day to ensure equitable day-off rotation
            self.worker_pool.rotate(-1)


# --- Recruitment & Onboarding Module ---

def recruit_new_worker(name, cert_status, source="Herb's Noon"):
    """Simulates the conversion of a lead from recruitment to an app user."""
    worker = Worker(name, cert_status, source)
    
    message = f"[Recruitment Success] Worker **'{worker.name}'** (ID: {worker.worker_id[:8]}...) onboarded from **{source}**."
    if not cert_status:
        st.warning(message + " **ALERT: Worker requires certification verification before scheduling.**")
    else:
        st.info(message)
        
    return worker


# --- Main Application Execution (Interactive Setup) ---

if __name__ == "__main__":
    st.set_page_config(layout="wide") 
    st.title("FlagPro Shift Scheduling System Simulation") 

    # ----------------------------------------------------
    # INPUT WIDGETS IN THE SIDEBAR (Interactive Controls)
    # ----------------------------------------------------
    st.sidebar.title("Scheduling Controls")
    
    # 1. Start Date Input
    default_start_date = datetime.now().date()
    start_date_obj = st.sidebar.date_input("Schedule Start Date", default_start_date)
    start_date_str = start_date_obj.isoformat()
    
    # 2. Cycle Length Input
    rotation_days = st.sidebar.number_input("Rotation Cycle Length (Days)", 
                                            min_value=7, max_value=365, value=28, step=7)
    
    # 3. Number of Cycles Input
    cycles = st.sidebar.slider("Number of Cycles to Generate", 
                               min_value=1, max_value=12, value=1)


    # --- 1. Initial Worker Pool (Mix of App and Herb's recruits) ---
    st.header("1. Initializing Worker Pool") 
    
    workers = [
        Worker("Alice J.", True, "App Signup"),
        Worker("Bob K.", True, "App Signup"),
        Worker("Charlie L.", True, "App Signup"),
        Worker("Dana M.", True, "App Signup"),
        Worker("Eve N.", True, "App Signup"),
    ]
    st.write(f"Initialized **{len(workers)}** certified workers from App Signups.")

    # --- 2. Recruitment & Onboarding Simulation ---
    st.header("2. Recruitment & Onboarding Simulation") 
    
    new_recruits = [
        recruit_new_worker("Frank O.", True),
        recruit_new_worker("Grace P.", False), # Uncertified recruit
    ]
    
    # Combine the worker pools
    all_workers = workers + new_recruits 
    st.success(f"Total Active Workers: **{len(all_workers)}**")

    # --- 3. Generate the Alternating Schedule ---
    st.header("3. Generating Alternating Schedule") 
    
    # Pass the total workers and the user-defined rotation days
    scheduler = AlternatingScheduler(all_workers, rotation_days=rotation_days) 
    scheduler.generate_loop_schedule(start_date_str, cycles=cycles) 

    # --- 4. Display a Snippet of the Generated Schedule ---
    st.header("4. Schedule Snippet (First 3 Days)") 
    
    dates_to_show = [
        (start_date_obj + timedelta(days=i)).isoformat()
        for i in range(3)
    ]

    for date_key in dates_to_show:
        st.subheader(f"Date: {date_key}") 
        
        if scheduler.schedule[date_key]:
            st.dataframe(
                scheduler.schedule[date_key],
                hide_index=True,
                column_order=['shift_type', 'start_time', 'end_time', 'worker_name']
            )
        else:
            st.write("No shifts scheduled.") 

    # --- 5. Example of Job Site Assignment (Dispatch Feature) ---
    job_1 = JobSite("Main Street Re-Pave", "123 Main St.", 2, "2025-10-01", "2025-10-05")

    st.header("5. Dispatching Simulation") 
    
    first_day_shifts = scheduler.schedule.get(dates_to_show[0], []) # Use .get to safely retrieve
    day_shift_worker = next((s for s in first_day_shifts if s['shift_type'] == 'Day'), None)
    swing_shift_worker = next((s for s in first_day_shifts if s['shift_type'] == 'Swing'), None)
    
    if day_shift_worker and swing_shift_worker:
        st.markdown(f"**{job_1.name}** requires {job_1.required_flaggers} flaggers on {dates_to_show[0]}.")
        st.success(f"DISPATCHED (Day Shift): **{day_shift_worker['worker_name']}**")
        st.success(f"DISPATCHED (Swing Shift): **{swing_shift_worker['worker_name']}**")
        st.write(f"Flaggers will use the app's geofencing feature to Clock In/Out at *{job_1.location}*.")
    else:
        st.error(f"Not enough scheduled shifts found for **{job_1.name}** on {dates_to_show[0]} to cover job requirements.")