"""
test_virtual_hardware.py -- Test suite for VAI-OS Virtual Hardware Layer

Tests all virtual hardware components: bus, cpu, memory, storage, nic,
display, io, firmware, sensors, radio, hooks, metrics, and full init.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import logging
logging.basicConfig(level=logging.WARNING)

import unittest
from aios.virt.hooks import HardwareHooks, get_hooks, INTROSPECT, LOG, METRICS
from aios.virt.metrics import HardwareMetrics, get_metrics
from aios.virt.firmware import VirtualFirmware
from aios.virt.bus import VirtualHardwareBus
from aios.virt.cpu import VirtualCPU, VirtualCore
from aios.virt.memory import VirtualMemory, ZONE_USER, ZONE_SYSTEM
from aios.virt.storage import VirtualStorage, BLOCK_SIZE
from aios.virt.nic import VirtualNIC, NetworkPacket
from aios.virt.display import VirtualDisplay, Frame
from aios.virt.io import VirtualIO, IOEvent, EVT_TOUCH_DOWN, EVT_BUTTON, EVT_USB_ATTACH
from aios.virt.sensors import VirtualSensors, SENSOR_BATTERY, SENSOR_GPS, ALL_SENSORS
from aios.virt.radio import VirtualRadio, RADIO_CELLULAR, RADIO_WIFI, RADIO_BLUETOOTH
from aios.virt import initialize_hardware, get_hardware_bus


class TestHardwareHooks(unittest.TestCase):
    def setUp(self):
        self.hooks = HardwareHooks()

    def test_register_and_fire(self):
        fired = []
        self.hooks.register(LOG, "test.event", lambda e, p: fired.append((e, p)))
        self.hooks.fire("test.event", {"val": 42})
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0], ("test.event", {"val": 42}))

    def test_fire_no_handler(self):
        # Should not raise
        self.hooks.fire("no.such.event", None)

    def test_history(self):
        self.hooks.fire("history.test", "payload")
        hist = self.hooks.get_history()
        self.assertTrue(any(h["event"] == "history.test" for h in hist))

    def test_list_hooks(self):
        self.hooks.register(METRICS, "m.event", lambda e, p: None)
        summary = self.hooks.list_hooks()
        self.assertIn("m.event", summary[METRICS])

    def test_hook_exception_swallowed(self):
        def bad_hook(e, p): raise RuntimeError("oops")
        self.hooks.register(LOG, "bad.event", bad_hook)
        self.hooks.fire("bad.event", None)  # should not raise

    def test_unregister(self):
        fired = []
        fn = lambda e, p: fired.append(1)
        self.hooks.register(LOG, "u.event", fn)
        self.hooks.unregister(LOG, "u.event", fn)
        self.hooks.fire("u.event", None)
        self.assertEqual(fired, [])


class TestHardwareMetrics(unittest.TestCase):
    def setUp(self):
        self.metrics = HardwareMetrics()

    def test_gauge(self):
        self.metrics.set_gauge("cpu.util", 0.75)
        self.assertAlmostEqual(self.metrics.get_gauge("cpu.util"), 0.75)

    def test_gauge_default(self):
        self.assertEqual(self.metrics.get_gauge("nonexistent", 99.0), 99.0)

    def test_counter(self):
        self.metrics.increment_counter("reads", 5)
        self.metrics.increment_counter("reads", 3)
        self.assertEqual(self.metrics.get_counter("reads"), 8)

    def test_histogram(self):
        for v in [1.0, 2.0, 3.0]:
            self.metrics.record_histogram("latency", v)
        stats = self.metrics.get_histogram_stats("latency")
        self.assertEqual(stats["min"], 1.0)
        self.assertEqual(stats["max"], 3.0)
        self.assertAlmostEqual(stats["mean"], 2.0)
        self.assertEqual(stats["count"], 3)

    def test_collect_snapshot(self):
        self.metrics.set_gauge("x", 1.0)
        snap = self.metrics.collect()
        self.assertIn("gauges", snap)
        self.assertIn("x", snap["gauges"])

    def test_list_metric_names(self):
        self.metrics.set_gauge("g1", 1)
        self.metrics.increment_counter("c1")
        names = self.metrics.list_metric_names()
        self.assertIn("g1", names["gauges"])
        self.assertIn("c1", names["counters"])


class TestVirtualFirmware(unittest.TestCase):
    def setUp(self):
        self.fw = VirtualFirmware()
        self.fw.initialize()

    def test_version(self):
        self.assertIn("VAIOS", self.fw.get_version())

    def test_boot_table(self):
        bt = self.fw.get_boot_table()
        self.assertIn("firmware_version", bt)
        self.assertIn("memory_map", bt)
        self.assertIn("capabilities", bt)

    def test_post_results(self):
        post = self.fw.get_post_results()
        self.assertIn("cpu", post)
        self.assertTrue(post["cpu"])

    def test_capability(self):
        self.assertTrue(self.fw.get_capability("crypto_accel"))

    def test_introspect(self):
        state = self.fw.introspect()
        self.assertTrue(state["initialized"])


class TestVirtualCPU(unittest.TestCase):
    def setUp(self):
        self.cpu = VirtualCPU(num_cores=2, freq_ghz=1.0)

    def test_init(self):
        self.assertEqual(self.cpu.num_cores, 2)
        self.assertEqual(len(self.cpu.cores), 2)

    def test_tick(self):
        self.cpu.tick()
        self.assertEqual(self.cpu.get_total_cycles(), 1)

    def test_execute_nop(self):
        self.cpu.execute("NOP", core_id=0)

    def test_execute_invalid(self):
        with self.assertRaises(ValueError):
            self.cpu.execute("BADOP", core_id=0)

    def test_utilization(self):
        self.cpu.set_core_utilization(0, 0.5)
        self.assertAlmostEqual(self.cpu.cores[0].utilization, 0.5)

    def test_introspect(self):
        state = self.cpu.introspect()
        self.assertEqual(state["num_cores"], 2)
        self.assertIn("cores", state)


class TestVirtualMemory(unittest.TestCase):
    def setUp(self):
        self.mem = VirtualMemory(capacity_mb=512)

    def test_allocate(self):
        block = self.mem.allocate(1024 * 1024, zone=ZONE_USER, tag="test")
        self.assertEqual(block.size, 1024 * 1024)
        self.assertEqual(block.zone, ZONE_USER)

    def test_free(self):
        block = self.mem.allocate(1024, tag="tmp")
        self.mem.free(block)
        self.assertEqual(len(self.mem.list_allocations()), 0)

    def test_oom(self):
        with self.assertRaises(MemoryError):
            self.mem.allocate(1024 * 1024 * 1024)  # 1 GB > 512 MB

    def test_read_write(self):
        data = self.mem.read(0x1000, 16)
        self.assertEqual(len(data), 16)
        self.mem.write(0x1000, b"hello")

    def test_pressure(self):
        mb = 1024 * 1024
        self.mem.allocate(100 * mb)
        pressure = self.mem.get_pressure()
        self.assertGreater(pressure, 0)
        self.assertLessEqual(pressure, 1.0)

    def test_introspect(self):
        state = self.mem.introspect()
        self.assertEqual(state["capacity_mb"], 512)


class TestVirtualStorage(unittest.TestCase):
    def setUp(self):
        self.stg = VirtualStorage(capacity_gb=4)

    def test_write_read_block(self):
        data = b"A" * BLOCK_SIZE
        self.stg.write_block(0, data)
        result = self.stg.read_block(0)
        self.assertEqual(result, data)

    def test_empty_block_returns_zeros(self):
        result = self.stg.read_block(1)
        self.assertEqual(result, bytes(BLOCK_SIZE))

    def test_invalid_lba(self):
        with self.assertRaises(ValueError):
            self.stg.read_block(-1)

    def test_partitions(self):
        parts = self.stg.get_partitions()
        names = [p.name for p in parts]
        self.assertIn("system", names)
        self.assertIn("user", names)

    def test_find_partition(self):
        p = self.stg.find_partition("system")
        self.assertIsNotNone(p)
        self.assertEqual(p.name, "system")

    def test_wrong_block_size(self):
        with self.assertRaises(ValueError):
            self.stg.write_block(0, b"short")


class TestVirtualNIC(unittest.TestCase):
    def setUp(self):
        self.nic = VirtualNIC()

    def test_send_recv(self):
        pkt = NetworkPacket("02:AA:AA:AA:AA:AA", "02:BB:BB:BB:BB:BB", b"hello", "TEST")
        self.nic.inject_packet(pkt)
        received = self.nic.recv()
        self.assertIsNotNone(received)
        self.assertEqual(received.payload, b"hello")

    def test_send_packet(self):
        pkt = NetworkPacket(self.nic.mac, "FF:FF:FF:FF:FF:FF", b"data")
        self.nic.send(pkt)
        drained = self.nic.drain_tx_queue()
        self.assertEqual(len(drained), 1)

    def test_link_down(self):
        self.nic.set_link_up(False)
        pkt = NetworkPacket(self.nic.mac, "FF:FF:FF:FF:FF:FF", b"x")
        with self.assertRaises(IOError):
            self.nic.send(pkt)

    def test_oversized_packet(self):
        pkt = NetworkPacket(self.nic.mac, "FF:FF:FF:FF:FF:FF", b"x" * 2000)
        with self.assertRaises(ValueError):
            self.nic.send(pkt)

    def test_recv_empty(self):
        result = self.nic.recv(timeout=0.0)
        self.assertIsNone(result)


class TestVirtualDisplay(unittest.TestCase):
    def setUp(self):
        self.dsp = VirtualDisplay(width=320, height=240)

    def test_render(self):
        frame = self.dsp.make_frame()
        self.dsp.render(frame)
        self.assertEqual(self.dsp._frames_rendered, 1)

    def test_wrong_resolution(self):
        frame = Frame(100, 100)
        with self.assertRaises(ValueError):
            self.dsp.render(frame)

    def test_power_off_skips_render(self):
        self.dsp.power_off()
        frame = self.dsp.make_frame()
        self.dsp.render(frame)
        self.assertEqual(self.dsp._frames_rendered, 0)

    def test_brightness(self):
        self.dsp.set_brightness(0.5)
        self.assertAlmostEqual(self.dsp._brightness, 0.5)

    def test_introspect(self):
        state = self.dsp.introspect()
        self.assertEqual(state["width"], 320)


class TestVirtualIO(unittest.TestCase):
    def setUp(self):
        self.io = VirtualIO()

    def test_touch_event(self):
        evt = IOEvent(EVT_TOUCH_DOWN, {"pos": (100, 200)})
        result = self.io.handle_event(evt)
        self.assertEqual(result["action"], "touch_start")

    def test_button_event(self):
        evt = IOEvent(EVT_BUTTON, {"button": "power", "pressed": True})
        result = self.io.handle_event(evt)
        self.assertEqual(result["action"], "button")
        self.assertEqual(result["button"], "power")

    def test_usb_attach(self):
        evt = IOEvent(EVT_USB_ATTACH, {})
        self.io.handle_event(evt)
        self.assertTrue(self.io.is_usb_connected())

    def test_poll_empty(self):
        self.assertIsNone(self.io.poll())

    def test_inject_and_poll(self):
        evt = IOEvent(EVT_BUTTON, {"button": "vol_up"})
        self.io.inject_event(evt)
        result = self.io.poll()
        self.assertIsNotNone(result)
        self.assertEqual(result.event_type, EVT_BUTTON)


class TestVirtualSensors(unittest.TestCase):
    def setUp(self):
        self.sns = VirtualSensors()

    def test_read_battery(self):
        val = self.sns.read(SENSOR_BATTERY)
        self.assertIn("level", val)
        self.assertGreaterEqual(val["level"], 0.0)
        self.assertLessEqual(val["level"], 1.0)

    def test_read_all(self):
        all_vals = self.sns.read_all()
        for s in ALL_SENSORS:
            self.assertIn(s, all_vals)

    def test_set_value(self):
        self.sns.set_value(SENSOR_GPS, {"lat": 37.7749, "lon": -122.4194, "alt_m": 10.0, "fix": True})
        val = self.sns.read(SENSOR_GPS)
        self.assertAlmostEqual(val["lat"], 37.7749)

    def test_invalid_sensor(self):
        with self.assertRaises(ValueError):
            self.sns.read("unicorn_sensor")

    def test_simulate_motion(self):
        import math
        self.sns.simulate_motion(math.pi)
        val = self.sns.read("accelerometer")
        self.assertAlmostEqual(val["z"], 9.81)


class TestVirtualRadio(unittest.TestCase):
    def setUp(self):
        self.radio = VirtualRadio()

    def test_all_radios_powered(self):
        for r in (RADIO_CELLULAR, RADIO_WIFI, RADIO_BLUETOOTH):
            self.assertTrue(self.radio.get_interface(r).is_powered())

    def test_transmit_receive(self):
        from aios.virt.radio import RadioPacket
        pkt = RadioPacket(RADIO_WIFI, 5180.0, b"data")
        self.radio.get_interface(RADIO_WIFI).inject_rx(pkt)
        result = self.radio.receive(RADIO_WIFI)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, b"data")

    def test_transmit_powered_off(self):
        self.radio.power_off(RADIO_BLUETOOTH)
        with self.assertRaises(IOError):
            self.radio.transmit(RADIO_BLUETOOTH, 2402.0, b"x")

    def test_rssi(self):
        self.radio.set_rssi(RADIO_CELLULAR, -80.0)
        self.assertAlmostEqual(self.radio.get_rssi(RADIO_CELLULAR), -80.0)

    def test_invalid_radio(self):
        with self.assertRaises(ValueError):
            self.radio.transmit("fax_machine", 1000.0, b"data")


class TestVirtualHardwareBus(unittest.TestCase):
    def setUp(self):
        self.bus = VirtualHardwareBus()

    def test_register_and_get(self):
        device = object()
        self.bus.register_device("testdev", device, "generic")
        self.assertIs(self.bus.get_device("testdev"), device)

    def test_duplicate_register(self):
        self.bus.register_device("dup", object())
        with self.assertRaises(ValueError):
            self.bus.register_device("dup", object())

    def test_enumerate_devices(self):
        self.bus.register_device("dev1", object(), "type_a")
        devices = self.bus.enumerate_devices()
        names = [d["name"] for d in devices]
        self.assertIn("dev1", names)

    def test_unregister(self):
        self.bus.register_device("tmp", object())
        self.bus.unregister_device("tmp")
        self.assertIsNone(self.bus.get_device("tmp"))

    def test_get_nonexistent(self):
        self.assertIsNone(self.bus.get_device("ghost"))


class TestInitializeHardware(unittest.TestCase):
    def test_full_init(self):
        bus = initialize_hardware(cpu_cores=2, memory_mb=512, storage_gb=4)
        self.assertIsNotNone(bus)
        devices = bus.enumerate_devices()
        names = [d["name"] for d in devices]
        for expected in ("cpu", "memory", "storage", "nic", "display", "io", "sensors", "radio", "firmware"):
            self.assertIn(expected, names)

    def test_get_hardware_bus(self):
        initialize_hardware()
        bus = get_hardware_bus()
        self.assertIsNotNone(bus)

    def test_cpu_accessible(self):
        bus = initialize_hardware()
        cpu = bus.get_device("cpu")
        self.assertIsNotNone(cpu)
        state = cpu.introspect()
        self.assertIn("num_cores", state)

    def test_metrics_populated(self):
        initialize_hardware()
        metrics = get_metrics()
        snap = metrics.collect()
        self.assertIn("gauges", snap)


if __name__ == "__main__":
    print("=" * 60)
    print("  VAI-OS Virtual Hardware Layer — Test Suite")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__("__main__"))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n[PASS] All virtual hardware tests passed.")
        print("[VIRT] Virtual Hardware Layer verified — boot handoff ready.")
    else:
        print("\n[FAIL] Some tests failed.")
        sys.exit(1)
