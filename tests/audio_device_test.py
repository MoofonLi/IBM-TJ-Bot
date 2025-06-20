import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np

# 參數設定
duration = 5  # 錄音秒數
filename = "record_test.wav"

# 列出錄音裝置
devices = sd.query_devices()
print("錄音裝置列表")
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        print(f"{i}: {d['name']}")

# 自動尋找 USB PnP Sound Device (你的麥克風)
input_index = None
for i, device in enumerate(devices):
    if "USB PnP Sound Device" in device['name'] and device['max_input_channels'] > 0:
        input_index = i
        print(f"已自動選擇錄音裝置: {device['name']} (index {i})")
        break

if input_index is None:
    print("沒有找到 USB 麥克風，請確認是否插好。")
    exit(1)

# 取得錄音裝置支援的預設採樣率
fs = int(devices[input_index]['default_samplerate'])

print("開始錄音")
recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16', device=input_index)
sd.wait()
print("錄音結束")

# 儲存成 wav
wavfile.write(filename, fs, recording)
print(f"錄音已儲存為 {filename}")

# 播放裝置搜尋（播放端選擇）
output_index = None
for i, device in enumerate(devices):
    if "USB Audio Device" in device['name'] and device['max_output_channels'] > 0:
        output_index = i
        print(f"已自動選擇播放裝置: {device['name']} (index {i})")
        break

if output_index is None:
    print("沒有找到 USB 音效卡，請確認是否插好。")
    exit(1)

# 讀取剛剛錄好的音檔並播放
print("開始播放剛剛的錄音")
fs2, data = wavfile.read(filename)
sd.play(data, samplerate=fs2, device=output_index)
sd.wait()
print("播放結束")
