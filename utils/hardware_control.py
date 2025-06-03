import RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip, Color
import time

class HardwareControl:
    def __init__(self, led_count=1, led_pin=18):
        GPIO.setmode(GPIO.BCM)  # 使用 BCM 引腳編號模式

        # 初始化伺服馬達引腳
        self.servo_pin = 7
        GPIO.setup(self.servo_pin, GPIO.OUT)
        self.servo = GPIO.PWM(self.servo_pin, 50)  # 50Hz
        self.servo.start(0)

        # 初始化 Neopixel LED
        self.led_count = led_count
        self.led_pin = led_pin
        self.strip = PixelStrip(led_count, led_pin, 800000, 10, False, 255, 0)
        self.strip.begin()

    def stop_servo_signal(self):
        """停止伺服馬達的PWM信號以避免抖動"""
        self.servo.ChangeDutyCycle(0)

    def wave(self):
        """讓伺服馬達揮手"""
        print("Waving...")
        self.servo.ChangeDutyCycle(7.5)  # 中間位置
        time.sleep(0.2)
        self.servo.ChangeDutyCycle(2.5)  # 左邊位置
        time.sleep(0.2)
        self.servo.ChangeDutyCycle(12.5)  # 右邊位置
        time.sleep(0.2)
        self.servo.ChangeDutyCycle(2.5)  # 左邊位置
        time.sleep(0.2)
        self.servo.ChangeDutyCycle(12.5)  # 右邊位置
        time.sleep(0.2)
        self.servo.ChangeDutyCycle(7.5)  # 回到中間位置
        time.sleep(0.2)
        self.stop_servo_signal()


    def lower_arm(self):
        """將伺服馬達移至下臂位置"""
        print("Lowering arm...")
        self.servo.ChangeDutyCycle(2.5)
        time.sleep(1)
        self.stop_servo_signal()


    def raise_arm(self):
        """將伺服馬達移至上臂位置"""
        print("Raising arm...")
        self.servo.ChangeDutyCycle(12.5)
        time.sleep(1)
        self.stop_servo_signal()


    def shine(self, color_name):
        """改變 Neopixel LED 顏色"""
        print(f"Shining {color_name} light...")
        color_map = {
            "red": Color(0, 255, 0),
            "green": Color(255, 0, 0),
            "blue": Color(0, 0, 255),
            "white": Color(255, 255, 255),
            "yellow": Color(128, 255, 0),
            "purple": Color(0, 255, 255),
            "orange": Color(64, 255, 0),
            "off": Color(0, 0, 0)
        }
        color = color_map.get(color_name.lower(), Color(255, 255, 255))  # 默認白色
        for i in range(self.led_count):
            self.strip.setPixelColor(i, color)
        self.strip.show()


    def dance(self):
        """執行一個完整的跳舞動作"""
        print("Dancing...")
        colors = ["red", "green", "blue", "white", "yellow", "purple", "orange" "off"]
        
        for i in range(3):
            # 揮手動作
            self.servo.ChangeDutyCycle(7.5)  # 中間
            time.sleep(0.2)
            self.servo.ChangeDutyCycle(2.5)  # 左
            self.shine(colors[i % len(colors)])
            time.sleep(0.2)
            self.servo.ChangeDutyCycle(12.5)  # 右
            time.sleep(0.2)
            self.servo.ChangeDutyCycle(7.5)  # 中間
            time.sleep(0.2)
        
        # 結束動作
        self.servo.ChangeDutyCycle(7.5)  # 回到中間
        time.sleep(0.5)
        self.stop_servo_signal()  # 停止PWM信號
        self.shine("off")  # 關閉燈光


    def cleanup(self):
        """清理 GPIO 引腳"""
        print("Cleaning up GPIO...")
        self.servo.stop()
        GPIO.cleanup()
