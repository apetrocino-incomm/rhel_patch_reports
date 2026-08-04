import tempfile
import unittest
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from report_generator import parse_inventory_file, build_html_report, parse_collected_host_file, filter_hosts_for_environment, summarize_reboot_counts, build_reboot_inventory


class ReportGeneratorTests(unittest.TestCase):
    def test_parse_inventory_file_collects_hosts(self):
        fixture = Path(__file__).parent / "fixtures" / "sample_inventory.ini"
        hosts = parse_inventory_file(fixture)
        self.assertEqual(len(hosts), 2)
        self.assertEqual(hosts[0]["hostname"], "host01.example.com")
        self.assertEqual(hosts[0]["ip"], "10.44.0.1")

    def test_parse_collected_host_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "samplehost"
            path.write_text("samplehost,10.42.0.10,2026-05-06,2026-02-13,2026-07-27,Red Hat Enterprise Linux release 8.10 (Ootpa),4.18.0-553.100.1.el8_10.x86_64,Reboot is required to fully utilize these updates.", encoding="utf-8")
            parsed = parse_collected_host_file(path)
            self.assertEqual(parsed["hostname"], "samplehost")
            self.assertEqual(parsed["ip"], "10.42.0.10")
            self.assertEqual(parsed["patch_status"], "Assessed")

    def test_parse_collected_host_file_without_reported_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "samplehost"
            path.write_text(
                "samplehost,10.42.0.10,2026-05-06,2026-02-13,Red Hat Enterprise Linux release 8.10 (Ootpa),4.18.0-553.100.1.el8_10.x86_64,Reboot should not be necessary.",
                encoding="utf-8",
            )
            parsed = parse_collected_host_file(path)
            self.assertEqual(parsed["hostname"], "samplehost")
            self.assertEqual(parsed["ip"], "10.42.0.10")
            self.assertEqual(parsed["os_release"], "Red Hat Enterprise Linux release 8.10 (Ootpa)")
            self.assertEqual(parsed["kernel"], "4.18.0-553.100.1.el8_10.x86_64")
            self.assertEqual(parsed["notes"], "Reboot should not be necessary.")

    def test_parse_collected_host_file_with_trailing_commas(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "samplehost"
            path.write_text(
                "samplehost,10.42.0.10,2026-05-06,2026-02-13,2026-07-27,Red Hat Enterprise Linux release 8.10 (Ootpa),4.18.0-553.100.1.el8_10.x86_64,Reboot should not be necessary.,",
                encoding="utf-8",
            )
            parsed = parse_collected_host_file(path)
            self.assertEqual(parsed["hostname"], "samplehost")
            self.assertEqual(parsed["ip"], "10.42.0.10")
            self.assertEqual(parsed["os_release"], "Red Hat Enterprise Linux release 8.10 (Ootpa)")
            self.assertEqual(parsed["kernel"], "4.18.0-553.100.1.el8_10.x86_64")
            self.assertEqual(parsed["notes"], "Reboot should not be necessary.")

    def test_filter_hosts_for_environment_uses_expected_subnets(self):
        hosts = [
            {"hostname": "lle1", "ip": "10.42.1.10"},
            {"hostname": "lle2", "ip": "10.44.2.20"},
            {"hostname": "cat3", "ip": "10.140.3.30"},
            {"hostname": "fcv", "ip": "10.141.4.40"},
            {"hostname": "other", "ip": "10.10.5.50"},
        ]

        lle_hosts = filter_hosts_for_environment(hosts, "LLE")
        cat3_hosts = filter_hosts_for_environment(hosts, "CAT3")
        fcv_hosts = filter_hosts_for_environment(hosts, "FCV_DMZ")

        self.assertEqual([host["hostname"] for host in lle_hosts], ["lle1", "lle2"])
        self.assertEqual([host["hostname"] for host in cat3_hosts], ["cat3"])
        self.assertEqual([host["hostname"] for host in fcv_hosts], ["fcv"])

    def test_summarize_reboot_counts_groups_notes_by_reboot_need(self):
        rows = [
            {"hostname": "a", "notes": "Reboot is required to fully utilize these updates."},
            {"hostname": "b", "notes": "Reboot should not be necessary."},
            {"hostname": "c", "notes": "Reboot is required to fully utilize these updates."},
            {"hostname": "d", "notes": "Reboot should not be necessary."},
        ]

        counts = summarize_reboot_counts(rows)
        self.assertEqual(counts["Reboot should not be necessary"], 2)
        self.assertEqual(counts["Reboot is probably not necessary"], 0)
        self.assertEqual(counts["Reboot is required to fully utilize these updates"], 2)

    def test_build_reboot_inventory_contains_required_hosts(self):
        rows = [
            {"hostname": "host1.example.com", "ip": "10.44.0.10", "notes": "Reboot is required to fully utilize these updates."},
            {"hostname": "host2.example.com", "ip": "10.44.0.11", "notes": "Reboot should not be necessary."},
        ]
        inventory = build_reboot_inventory(rows)
        self.assertIn("host1.example.com ansible_host=10.44.0.10", inventory)
        self.assertNotIn("host2.example.com", inventory)

    def test_build_html_report_contains_sections(self):
        rows = [
            {
                "hostname": "host01.example.com",
                "ip": "10.44.0.1",
                "patch_date": "2026-07-20",
                "last_reboot": "2026-07-18 08:00",
                "os_release": "Red Hat Enterprise Linux 8.10",
                "patch_status": "Needs reboot",
                "notes": "Reboot required",
                "source": "QTS_RHEL_LWR.ini",
            }
        ]
        issues = [
            {
                "hostname": "host02.example.com",
                "ip": "10.44.0.2",
                "issue": "Connection timed out",
                "source": "QTS_RHEL_LWR.ini",
            }
        ]
        report = build_html_report(rows, issues, title="Primary Report")
        self.assertIn("Primary Report", report)
        self.assertIn("host01.example.com", report)
        self.assertIn("Connection timed out", report)

    def test_build_html_report_includes_reboot_inventory_download_link(self):
        rows = [
            {
                "hostname": "host01.example.com",
                "ip": "10.44.0.1",
                "patch_date": "2026-07-20",
                "last_reboot": "2026-07-18 08:00",
                "os_release": "Red Hat Enterprise Linux 8.10",
                "patch_status": "Needs reboot",
                "notes": "Reboot is required to fully utilize these updates.",
                "source": "QTS_RHEL_LWR.ini",
            }
        ]
        issues = []
        report = build_html_report(
            rows,
            issues,
            title="Primary Report",
            reboot_inventory_filename="LLE_to_reboot.ini",
            reboot_inventory_content="host01.example.com ansible_host=10.44.0.1\n",
        )
        self.assertIn("download=\"LLE_to_reboot.ini\"", report)
        self.assertIn("data:text/plain;charset=utf-8,host01.example.com%20ansible_host%3D10.44.0.1%0A", report)
        self.assertIn("Download reboot inventory (1 host): LLE_to_reboot.ini", report)

    def test_build_html_report_includes_logo_and_footer(self):
        rows = []
        issues = []
        report = build_html_report(rows, issues, title="Logo Footer Report")
        self.assertIn("https://www.incomm.com/wp-content/uploads/2022/04/incomm_payments_logo_hrz.png__1200x372_q85_subsampling-2-2.png", report)
        self.assertIn("This report was generated by an automation created by Unix team. Report any mismatch to apetrocino@incomm.com", report)


if __name__ == "__main__":
    unittest.main()
