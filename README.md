# Club Tier Ranking (CTR) System

The **Club Tier Ranking (CTR) System** is a web-based application designed for the School of Computing Council to manage and evaluate student clubs. It automates the calculation of performance scores, assigns tiers (A/B/C/D), and generates transparent rankings based on event metrics.

## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [Project Overview](#project-overview)
3. [File Descriptions](#file-descriptions)
4. [How It Works](#how-it-works)

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- `pip` (Python package manager)

### Steps

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd ctr_project
    ```

2.  **Create a Virtual Environment (Optional but Recommended)**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Apply Database Migrations**
    Initialize the SQLite database with the required tables.
    ```bash
    python manage.py migrate
    ```

5.  **Create an Admin User**
    You need an admin account to manage clubs and events.
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to set a username (e.g., `admin`) and password.

6.  **Run the Development Server**
    ```bash
    python manage.py runserver
    ```

7.  **Access the Application**
    -   **Dashboard (Rankings):** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
    -   **Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Project Overview

The system is built using **Django**. It follows a standard Model-View-Template (MVT) architecture. The core logic for scoring and ranking is decoupled into a service layer triggered by signals, ensuring real-time updates whenever data changes.

### Key Features
-   **Automated Scoring:** Calculates Composite Performance Score (CPS) from 5 metrics (Planning, Execution, Documentation, Innovation, Turnout).
-   **Tier Assignment:** Automatically assigns tiers (A, B, C, D) based on CPS.
-   **Real-time Ranking:** Rankings update immediately when event scores are modified.
-   **Audit Logging:** Tracks who changed what, preserving data integrity.
-   **CSV Export:** Allows downloading ranking data for offline analysis.

---

## File Descriptions

Here is a breakdown of the key files in the project:

### Root Directory
-   `manage.py`: The command-line utility for administrative tasks (running server, migrations, etc.).
-   `requirements.txt`: Lists the Python dependencies required to run the project.

### `ctr_project/` (Project Configuration)
-   `settings.py`: Global configuration (database setup, installed apps, middleware, static files).
-   `urls.py`: The main URL routing entry point. It includes the admin site and delegates other routes to the `core` app.

### `core/` (Main Application)

#### Data & Logic
-   **`models.py`**: Defines the database schema.
    -   `Club`: Stores club details (name, leads, code).
    -   `Semester`: Manages academic periods.
    -   `Event`: Stores event data and the 5 scoring metrics (0-20).
    -   `Ranking`: Stores the calculated CPS, Tier, and Rank for a club in a semester.
    -   `AuditLog`: records changes to data for accountability.
-   **`services.py`**: Contains the business logic.
    -   `calculate_club_performance(club, semester)`: Aggregates event scores to compute CPS and determine Tier.
    -   `update_semester_ranks(semester)`: Sorts clubs by CPS and assigns sequential ranks.
    -   `signals`: Listeners that trigger calculations automatically when an Event is saved or deleted.
-   **`middleware.py`**:
    -   `CurrentUserMiddleware`: Captures the logged-in user making a request so that `AuditLog` can record who performed an action.

#### Interface (Views & Templates)
-   **`views.py`**: Handles HTTP requests.
    -   `DashboardView`: Displays the main ranking table.
    -   `ClubDetailView`: Shows detailed performance breakdown for a specific club.
    -   `export_rankings_csv`: Generates a CSV file of the current rankings.
-   **`urls.py`**: Maps URLs (like `/club/1/`) to the corresponding views.
-   **`admin.py`**: Configures the built-in Django Admin interface. Customizes how Clubs and Events are listed and edited.

#### Tests
-   **`tests.py`**: Contains automated tests to verify that CPS calculation, tier assignment, and sorting logic work correctly.

---

## How It Works

1.  **Data Entry**:
    -   An **Admin** logs into the Admin Panel.
    -   They create a `Semester` (e.g., "Fall 2024").
    -   They add `Club` entries.
    -   When a club hosts an event, the Admin adds an `Event` entry and inputs scores (0-20) for the 5 metrics.

2.  **Automatic Calculation (The "Magic")**:
    -   When the Admin clicks **Save** on an Event:
        1.  A **Signal** in `services.py` intercepts the save action.
        2.  It calls `calculate_club_performance`, which:
            -   Averages the scores for all events the club has done in that semester.
            -   Sums the averages to get the **CPS** (0-100).
            -   Assigns a **Tier** (A if >90, B if >75, etc.).
            -   Updates the `Ranking` table.
        3.  It then calls `update_semester_ranks`, which re-orders all clubs in that semester based on their new CPS.

3.  **Audit Logging**:
    -   Simultaneously, the system compares the old data with the new data.
    -   It creates an `AuditLog` entry (e.g., "Event 'Hackathon' updated. Execution Score: 15 -> 18").

4.  **Visualization**:
    -   Users (Council, Dean, HoD) visit the **Dashboard**.
    -   They see the live, ranked list of clubs.
    -   Clicking "View" on a club shows the `ClubDetail` page with charts (progress bars) and a history of their events.
