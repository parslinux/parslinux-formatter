#!/usr/bin/env python3
"""ParsLinux Formatter — Birim Test Paketi (test_formatter.py)."""

import os
import sys
import unittest

# src dizinini import yoluna ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from Utils import format_duration, format_size, request_stop, stop_requested
import USBDeviceManager
from USBDeviceManager import DriveError, get_block_name, CRITICAL_MOUNT_POINTS, validate_usb_drive
import CLI


class TestUtils(unittest.TestCase):
    def test_format_size(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(500), "500.0 B")
        self.assertEqual(format_size(1000 * 1000), "1.0 MB")
        self.assertEqual(format_size(15 * 1000 * 1000 * 1000), "15.0 GB")

    def test_format_duration(self):
        self.assertEqual(format_duration(None), "--:--")
        self.assertEqual(format_duration(-5), "--:--")
        self.assertEqual(format_duration(45), "00:45")
        self.assertEqual(format_duration(125), "02:05")
        self.assertEqual(format_duration(3665), "01:01:05")

    def test_stop_signal(self):
        self.assertFalse(stop_requested())
        request_stop()
        self.assertTrue(stop_requested())


class TestDeviceManager(unittest.TestCase):
    def test_get_block_name(self):
        self.assertEqual(get_block_name("/dev/sdb"), "sdb")
        self.assertEqual(get_block_name("sdb"), "sdb")
        self.assertEqual(get_block_name("/dev/sdc"), "sdc")
        self.assertEqual(get_block_name("/dev/mmcblk0"), "mmcblk0")
        self.assertEqual(get_block_name("/dev/nvme0n1"), "nvme0n1")
        self.assertIsNone(get_block_name(""))
        self.assertIsNone(get_block_name("/dev/null"))
        self.assertIsNone(get_block_name("../etc/passwd"))

    def test_critical_mounts(self):
        self.assertIn("/", CRITICAL_MOUNT_POINTS)
        self.assertIn("/boot", CRITICAL_MOUNT_POINTS)
        self.assertIn("/home", CRITICAL_MOUNT_POINTS)

    def test_safety_validation_rejects_invalid(self):
        # Var olmayan veya güvenli olmayan aygıtların DriveError fırlattığını doğrula
        with self.assertRaises(DriveError):
            validate_usb_drive("nonexistent_device_xyz_123")


class TestCLIHelpers(unittest.TestCase):
    def test_version_retrieval(self):
        ver = CLI.get_version()
        self.assertIn(".", ver)
        self.assertTrue(len(ver) >= 3)

    def test_ansi_bar_rendering(self):
        bar = CLI.render_ansi_bar(50.0, 42.5, "00:15")
        self.assertIn("50.0%", bar)
        self.assertIn("42.5 MB/s", bar)
        self.assertIn("00:15", bar)


if __name__ == "__main__":
    unittest.main()
