import pyaudio
import wave

# 參數設定
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 3
WAVE_OUTPUT_FILENAME = "output.wav"

# 初始化PyAudio
audio = pyaudio.PyAudio()

# 開啟麥克風串流
stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=0,  # <<<<<< 指定這裡！！！！
                    frames_per_buffer=CHUNK)

print("開始錄音...")

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK, exception_on_overflow=False)
    frames.append(data)

print("錄音完成。")

# 停止錄音
stream.stop_stream()
stream.close()
audio.terminate()

# 存檔
wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(audio.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

print(f"已經把錄音存成 {WAVE_OUTPUT_FILENAME}")
