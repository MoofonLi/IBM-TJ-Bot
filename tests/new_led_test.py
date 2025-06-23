import time
import math
import board
import neopixel
import colorsys


def main():

    num_pixels = 1  # LED 數量，可改為你的實際數量
    pixels = neopixel.NeoPixel(board.D13, num_pixels, brightness=1.0, auto_write=False, pixel_order=neopixel.RGB)
    try:
        hue = 0.0  # 色相初始值
        while True:
            for i in range(0, 360, 2):  # 呼吸波：0~360 度
                # 計算亮度（呼吸節奏）
                breath = (math.sin(math.radians(i)) + 1) / 2  # 範圍 0~1
                # HSV 轉 RGB（色相持續變化，飽和度與亮度為1）
                r, g, b = colorsys.hsv_to_rgb(hue, 1, breath)
                rgb = (int(r * 255), int(g * 255), int(b * 255))
                pixels.fill(rgb)
                pixels.show()
                time.sleep(0.02)
                hue += 0.002  # 色相平滑改變，彩虹顏色循環
                if hue > 1:
                    hue -= 1
    except KeyboardInterrupt:
        pixels.fill((0, 0, 0))
        pixels.show()


if __name__ == "__main__":
    main()