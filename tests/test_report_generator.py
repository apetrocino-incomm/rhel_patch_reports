import tempfile
import unittest
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from report_generator import ANSIBLE_INVENTORY_DIR, DEFAULT_INVENTORY_DIR, DEFAULT_INVENTORY_FILES, collect_host_data, discover_hosts, find_collected_host_file, hostname_prefix, parse_inventory_file, build_html_report, parse_collected_host_file, filter_hosts_for_environment, summarize_reboot_counts, build_reboot_inventory


class ReportGeneratorTests(unittest.TestCase):
    def test_hostname_prefix_ignores_fqdn(self):
        self.assertEqual(hostname_prefix("dplepl01v.uss.net"), "dplepl01v")
        self.assertEqual(hostname_prefix("dplepl01v"), "dplepl01v")

    def test_find_collected_host_file_matches_short_inventory_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inventory_dir = Path(tmpdir)
            collected_file = inventory_dir / "aplolsk8ctl02rd"
            collected_file.write_text("aplolsk8ctl02rd,10.83.161.221,2026-08-25,2026-07-21,2026-09-07,Red Hat Enterprise Linux release 8.10,4.18.0,Reboot is required to fully utilize these updates.", encoding="utf-8")

            self.assertEqual(find_collected_host_file("aplolsk8ctl02rd.incommrde.com", inventory_dir), collected_file)

    def test_collect_host_data_preserves_ansible_name_when_short_file_matches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inventory_dir = Path(tmpdir)
            (inventory_dir / "dplepl01v").write_text("dplepl01v,10.190.4.127,2026-08-25,2026-05-26,2026-09-07,Red Hat Enterprise Linux release 8.10,4.18.0,Reboot is required to fully utilize these updates.", encoding="utf-8")

            parsed = collect_host_data(
                {"hostname": "dplepl01v.uss.net", "ip": "10.190.4.127", "source": "QTS_RHEL_PRD.ini"},
                inventory_dir,
            )

            self.assertEqual(parsed["hostname"], "dplepl01v.uss.net")
            self.assertEqual(parsed["collected_hostname"], "dplepl01v")
            self.assertEqual(parsed["patch_status"], "Assessed")

    def test_discover_hosts_removes_duplicate_fqdn_prefixes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "OLS_ATL_PRD.ini"
            second = Path(tmpdir) / "OLS_ATL_PRD_EVN.ini"
            first.write_text("aplolsk8ctl02rd.incommrde.com ansible_host=10.83.161.221\n", encoding="utf-8")
            second.write_text("aplolsk8ctl02rd.incommrde.com ansible_host=10.83.161.221\n", encoding="utf-8")

            hosts = discover_hosts([str(first), str(second)])

            self.assertEqual(len(hosts), 1)

    def test_inventory_sources_use_git_inventory_and_inventory_comparison_dir(self):
        expected_files = {
            "Azure_LWR.ini",
            "OLS_ATL_LWR.ini",
            "OLS_QTS_LWR.ini",
            "QTS_CENTOS_LWR.ini",
            "QTS_LWR_IPA.ini",
            "QTS_OEL_LWR.ini",
            "QTS_RHEL_LWR.ini",
            "Azure_PRD.ini",
            "OLS_ATL_PRD_EVN.ini",
            "OLS_ATL_PRD.ini",
            "OLS_ATL_PRD_ODD.ini",
            "OLS_QTS_PRD_EVN.ini",
            "OLS_QTS_PRD.ini",
            "OLS_QTS_PRD_ODD.ini",
            "QTS_CENTOS_PRD.ini",
            "QTS_OEL_PRD.ini",
            "QTS_PRD_IPA.ini",
            "QTS_RHEL_PRD.ini",
            "GRATISCARD.ini",
            "DATAWAVE.ini",
        }

        self.assertEqual(ANSIBLE_INVENTORY_DIR, Path("/git_incomm/incomm_git_inventory"))
        self.assertEqual(DEFAULT_INVENTORY_DIR, Path("/inventory"))
        self.assertEqual({Path(path).name for path in DEFAULT_INVENTORY_FILES}, expected_files)
        self.assertTrue(all(Path(path).parent == ANSIBLE_INVENTORY_DIR for path in DEFAULT_INVENTORY_FILES))

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
