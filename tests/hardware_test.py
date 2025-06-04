from hardware_control import HardwareControl
import time

def test_hardware():
    try:
        # 初始化 HardwareControl
        hardware = HardwareControl(led_count=1, led_pin=18)

        print("Testing servo motor: Raising arm...")
        hardware.raise_arm()
        time.sleep(1)

        print("Testing servo motor: Lowering arm...")
        hardware.lower_arm()
        time.sleep(1)

        print("Testing servo motor: Waving...")
        hardware.wave()
        time.sleep(1)

        print("Testing Neopixel LED: Shining red...")
        hardware.shine("red")
        time.sleep(1)

        print("Testing Neopixel LED: Shining green...")
        hardware.shine("green")
        time.sleep(1)

        print("Testing Neopixel LED: Shining blue...")
        hardware.shine("blue")
        time.sleep(1)

        print("Testing Neopixel LED: Turning off...")
        hardware.shine("off")
        time.sleep(1)

    except KeyboardInterrupt:
        print("Test interrupted by user.")
    finally:
        print("Cleaning up hardware...")
        hardware.cleanup()

if __name__ == "__main__":
    test_hardware()
