import os
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


# Optional GUI/reporting dependencies are not required for database logic tests.
if "matplotlib" not in sys.modules:
    sys.modules.setdefault("matplotlib", types.ModuleType("matplotlib"))
    pyplot = types.ModuleType("matplotlib.pyplot")
    sys.modules["matplotlib.pyplot"] = pyplot
    sys.modules["matplotlib.backends"] = types.ModuleType("matplotlib.backends")
    tkagg = types.ModuleType("matplotlib.backends.backend_tkagg")
    tkagg.FigureCanvasTkAgg = object
    sys.modules["matplotlib.backends.backend_tkagg"] = tkagg

if "fpdf" not in sys.modules:
    fpdf = types.ModuleType("fpdf")
    fpdf.FPDF = object
    sys.modules["fpdf"] = fpdf

import Aceestver


class AceestDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        self.original_db_name = Aceestver.DB_NAME
        Aceestver.DB_NAME = self.db_path
        Aceestver.init_db()
        self.conn = sqlite3.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        Aceestver.DB_NAME = self.original_db_name
        self.temp_dir.cleanup()

    def test_init_db_creates_default_admin(self):
        row = self.conn.execute(
            "SELECT username, password, role FROM users WHERE username='admin'"
        ).fetchone()
        self.assertEqual(row, ("admin", "admin", "Admin"))

    def test_init_db_creates_all_required_tables(self):
        tables = {
            row[0]
            for row in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        self.assertTrue(
            {"users", "clients", "progress", "workouts", "exercises", "metrics"}
            <= tables
        )


class AceestAppLogicTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        self.original_db_name = Aceestver.DB_NAME
        Aceestver.DB_NAME = self.db_path
        Aceestver.init_db()

        self.app = Aceestver.ACEestApp.__new__(Aceestver.ACEestApp)
        self.app.conn = sqlite3.connect(self.db_path)
        self.app.cur = self.app.conn.cursor()
        self.app.current_client = None
        self.app.program_templates = {
            "Fat Loss": ["Full Body HIIT"],
            "Muscle Gain": ["Push/Pull/Legs"],
            "Beginner": ["Full Body 3x/week"],
        }

    def tearDown(self):
        self.app.conn.close()
        Aceestver.DB_NAME = self.original_db_name
        self.temp_dir.cleanup()

    def test_add_save_client_inserts_active_client(self):
        self.app.refresh_client_list = lambda: None
        with patch("Aceestver.simpledialog.askstring", return_value="Alice"), patch(
            "Aceestver.messagebox.showinfo"
        ):
            self.app.add_save_client()

        row = self.app.cur.execute(
            "SELECT name, membership_status FROM clients WHERE name='Alice'"
        ).fetchone()
        self.assertEqual(row, ("Alice", "Active"))

    def test_add_save_client_ignores_cancelled_entry(self):
        self.app.refresh_client_list = lambda: None
        with patch("Aceestver.simpledialog.askstring", return_value=None), patch(
            "Aceestver.messagebox.showinfo"
        ):
            self.app.add_save_client()

        count = self.app.cur.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        self.assertEqual(count, 0)

    def test_generate_program_updates_selected_client(self):
        self.app.cur.execute(
            "INSERT INTO clients (name, membership_status) VALUES ('Alice', 'Active')"
        )
        self.app.conn.commit()
        self.app.current_client = "Alice"
        self.app.refresh_summary = lambda: None

        with patch("Aceestver.random.choice", side_effect=lambda values: values[0]), patch(
            "Aceestver.messagebox.showinfo"
        ):
            self.app.generate_program()

        program = self.app.cur.execute(
            "SELECT program FROM clients WHERE name='Alice'"
        ).fetchone()[0]
        self.assertEqual(program, "Full Body HIIT")

    def test_check_membership_handles_missing_renewal_date(self):
        self.app.cur.execute(
            "INSERT INTO clients (name, membership_status, membership_end) "
            "VALUES ('Alice', 'Active', NULL)"
        )
        self.app.conn.commit()
        self.app.current_client = "Alice"

        with patch("Aceestver.messagebox.showinfo") as showinfo:
            self.app.check_membership()

        showinfo.assert_called_once_with(
            "Membership", "Membership: Active\nRenewal Date: N/A"
        )

    def test_login_accepts_valid_credentials(self):
        class StringVar:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

        self.app.username_var = StringVar("admin")
        self.app.password_var = StringVar("admin")
        self.app.dashboard = lambda: None

        self.app.login()

        self.assertEqual(self.app.current_user, "admin")
        self.assertEqual(self.app.current_role, "Admin")

    def test_login_rejects_invalid_credentials(self):
        class StringVar:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

        self.app.username_var = StringVar("admin")
        self.app.password_var = StringVar("wrong")
        self.app.dashboard = lambda: None

        with patch("Aceestver.messagebox.showerror") as showerror:
            self.app.login()

        showerror.assert_called_once_with("Login Failed", "Invalid credentials")


if __name__ == "__main__":
    unittest.main()
