import unittest
import os
from database import get_connection, init_db
import HtmlTestRunner

class TestRadioDatabase(unittest.TestCase):
    def setUp(self):
        init_db()
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def test_add_radio(self):
        self.cursor.execute("INSERT INTO radios (radio_id, serial, model) VALUES (?, ?, ?)",
                            ("TEST123", "SN0001", "ModelA"))
        self.conn.commit()

        self.cursor.execute("SELECT * FROM radios WHERE radio_id = ?", ("TEST123",))
        row = self.cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[2], "SN0001")  # serial

    def test_change_radio_status(self):
        self.cursor.execute("INSERT INTO radios (radio_id, serial, model) VALUES (?, ?, ?)",
                            ("TEST124", "SN0002", "ModelB"))
        self.conn.commit()

        self.cursor.execute("UPDATE radios SET status = ? WHERE radio_id = ?", ("In Service", "TEST124"))
        self.conn.commit()

        self.cursor.execute("SELECT status FROM radios WHERE radio_id = ?", ("TEST124",))
        status = self.cursor.fetchone()[0]
        self.assertEqual(status, "In Service")

    def test_delete_radio(self):
        # Add test radio
        self.cursor.execute("INSERT INTO radios (radio_id, serial, model) VALUES (?, ?, ?)",
                            ("TEST125", "SN0003", "ModelC"))
        self.conn.commit()

        # Delete test radio
        self.cursor.execute("DELETE FROM radios WHERE radio_id = ?", ("TEST125",))
        self.conn.commit()

        # Ensure it's gone
        self.cursor.execute("SELECT * FROM radios WHERE radio_id = ?", ("TEST125",))
        result = self.cursor.fetchone()
        self.assertIsNone(result)

    def test_log_radio_change(self):
      # Add a test radio
      self.cursor.execute("INSERT INTO radios (radio_id, serial, model) VALUES (?, ?, ?)",
                          ("TEST126", "SN0004", "ModelD"))
      self.conn.commit()

      # Get inserted radio's internal ID
      self.cursor.execute("SELECT id FROM radios WHERE radio_id = ?", ("TEST126",))
      radio_id = self.cursor.fetchone()[0]

      # Log a change
      from database import log_radio_change
      log_radio_change(self.cursor, radio_id, "UPDATE", "model", "ModelD", "ModelE")
      self.conn.commit()

      # Verify the log
      self.cursor.execute("""
          SELECT change_type, field_changed, old_value, new_value
          FROM radio_changes
          WHERE radio_id = ? ORDER BY timestamp DESC LIMIT 1
      """, (radio_id,))
      change = self.cursor.fetchone()

      self.assertIsNotNone(change)
      self.assertEqual(change[0], "UPDATE")
      self.assertEqual(change[1], "model")
      self.assertEqual(change[2], "ModelD")
      self.assertEqual(change[3], "ModelE")

    def test_toggle_missing_status(self):
      self.cursor.execute("INSERT INTO radios (radio_id, serial, model, missing) VALUES (?, ?, ?, ?)",
                          ("TEST127", "SN0005", "ModelE", "No"))
      self.conn.commit()

      # Toggle to Yes
      self.cursor.execute("UPDATE radios SET missing = ? WHERE radio_id = ?", ("Yes", "TEST127"))
      self.conn.commit()

      self.cursor.execute("SELECT missing FROM radios WHERE radio_id = ?", ("TEST127",))
      missing = self.cursor.fetchone()[0]
      self.assertEqual(missing, "Yes")

    def test_add_service_record(self):
      self.cursor.execute("INSERT INTO radios (radio_id, serial, model) VALUES (?, ?, ?)",
                          ("TEST128", "SN0006", "ModelF"))
      self.conn.commit()

      self.cursor.execute("SELECT id FROM radios WHERE radio_id = ?", ("TEST128",))
      radio_id = self.cursor.fetchone()[0]

      self.cursor.execute("""
          INSERT INTO services (radio_id, status, date_service, lrc_service_num, problem)
          VALUES (?, 'open', DATE('now'), 'LRC001', 'Won’t power on')
      """, (radio_id,))
      self.conn.commit()

      self.cursor.execute("SELECT * FROM services WHERE radio_id = ?", (radio_id,))
      service = self.cursor.fetchone()
      self.assertIsNotNone(service)
      self.assertEqual(service[4], "LRC001")  # LRC #

    def tearDown(self):
        self.conn.close()

if __name__ == "__main__":
    unittest.main(
        testRunner=HtmlTestRunner.HTMLTestRunner(
            output="test_report",
            report_name="RadioInventoryTestReport",
            combine_reports=True,
            add_timestamp=True
        )
    )
