from rpi_ws281x import PixelStrip, Color

LED_COUNT = 1  # LED 燈的數量
LED_PIN = 18   # GPIO 引腳

strip = PixelStrip(LED_COUNT, LED_PIN, 800000, 10, False, 255, 0)
strip.begin()

# 亮紅燈
strip.setPixelColor(0, Color(255, 0, 0))
strip.show()
input("Press Enter to turn off the LED...")
# 關閉 LED
strip.setPixelColor(0, Color(0, 0, 0))
strip.show()

