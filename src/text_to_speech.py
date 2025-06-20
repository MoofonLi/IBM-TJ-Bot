import os
import sounddevice as sd
import wave
import numpy as np
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class TextToSpeech:
    def __init__(self, apikey, url):
        self.authenticator = IAMAuthenticator(apikey)
        self.text_to_speech = TextToSpeechV1(authenticator=self.authenticator)
        self.text_to_speech.set_service_url(url)
        
        # 尋找音訊裝置
        devices = sd.query_devices()
        self.output_index = None
        
        for i, device in enumerate(devices):
            if "USB Audio Device" in device['name'] and device['max_output_channels'] > 0:
                self.output_index = i
                print(f"已自動選擇播放裝置: {device['name']} (index {i})")
                break

    def read_wav_with_wave_module(self, filename):
        """使用 Python 內建的 wave 模組讀取（更寬容）"""
        try:
            with wave.open(filename, 'rb') as wav_file:
                # 獲取音檔參數
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                
                print(f"音檔資訊: {sample_rate}Hz, {channels}聲道, {sample_width}bytes/樣本")
                
                # 讀取音檔數據
                raw_audio = wav_file.readframes(frames)
                
                # 轉換為 numpy array
                if sample_width == 1:
                    # 8-bit
                    audio_data = np.frombuffer(raw_audio, dtype=np.uint8)
                    audio_data = (audio_data.astype(np.float32) - 128) / 128.0
                elif sample_width == 2:
                    # 16-bit
                    audio_data = np.frombuffer(raw_audio, dtype=np.int16)
                    audio_data = audio_data.astype(np.float32) / 32768.0
                elif sample_width == 4:
                    # 32-bit
                    audio_data = np.frombuffer(raw_audio, dtype=np.int32)
                    audio_data = audio_data.astype(np.float32) / 2147483648.0
                else:
                    raise ValueError(f"不支援的樣本寬度: {sample_width}")
                
                # 處理多聲道
                if channels > 1:
                    audio_data = audio_data.reshape(-1, channels)
                
                return sample_rate, audio_data
                
        except Exception as e:
            print(f"wave 模組讀取失敗: {e}")
            return None, None

    def read_wav_manual(self, filename):
        """手動解析 WAV 檔案（完全忽略檔案大小問題）"""
        try:
            with open(filename, 'rb') as f:
                # 跳過 RIFF header (前12 bytes)
                f.seek(12)
                
                # 尋找 fmt chunk
                while True:
                    chunk_header = f.read(8)
                    if len(chunk_header) < 8:
                        break
                    
                    chunk_id = chunk_header[:4]
                    chunk_size = int.from_bytes(chunk_header[4:8], 'little')
                    
                    if chunk_id == b'fmt ':
                        # 讀取 fmt chunk
                        fmt_data = f.read(chunk_size)
                        
                        # 解析 fmt 資訊
                        audio_format = int.from_bytes(fmt_data[0:2], 'little')
                        channels = int.from_bytes(fmt_data[2:4], 'little')
                        sample_rate = int.from_bytes(fmt_data[4:8], 'little')
                        bytes_per_second = int.from_bytes(fmt_data[8:12], 'little')
                        block_align = int.from_bytes(fmt_data[12:14], 'little')
                        bits_per_sample = int.from_bytes(fmt_data[14:16], 'little')
                        
                        print(f"手動解析: {sample_rate}Hz, {channels}聲道, {bits_per_sample}bits")
                        
                    elif chunk_id == b'data':
                        # 找到數據，讀取音訊內容
                        print(f"找到音訊數據，大小: {chunk_size} bytes")
                        
                        # 直接讀取到檔案結尾（忽略 chunk_size）
                        current_pos = f.tell()
                        f.seek(0, 2)  # 移到檔案結尾
                        file_end = f.tell()
                        f.seek(current_pos)  # 回到數據開始位置
                        
                        actual_data_size = file_end - current_pos
                        print(f"實際可讀取大小: {actual_data_size} bytes")
                        
                        # 讀取實際數據
                        audio_bytes = f.read(actual_data_size)
                        
                        # 轉換為 numpy array
                        if bits_per_sample == 16:
                            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                            audio_data = audio_data.astype(np.float32) / 32768.0
                        elif bits_per_sample == 8:
                            audio_data = np.frombuffer(audio_bytes, dtype=np.uint8)
                            audio_data = (audio_data.astype(np.float32) - 128) / 128.0
                        else:
                            raise ValueError(f"不支援的位元深度: {bits_per_sample}")
                        
                        # 處理多聲道
                        if channels > 1:
                            audio_data = audio_data.reshape(-1, channels)
                        
                        return sample_rate, audio_data
                    else:
                        # 跳過其他 chunk
                        f.seek(chunk_size, 1)
                        
            return None, None
            
        except Exception as e:
            print(f"手動解析失敗: {e}")
            return None, None

    def speak(self, text):
        """生成語音並播放（完全避開 scipy）"""
        audio_filename = 'tts_output.wav'
        
        try:
            # 1. 生成音檔
            print(f"正在生成語音: {text}")
            with open(audio_filename, 'wb') as audio_file:
                response = self.text_to_speech.synthesize(
                    text,
                    voice='en-US_AllisonV3Voice',
                    accept='audio/wav'
                ).get_result()
                audio_file.write(response.content)
            
            print(f"音檔已保存為 {audio_filename}")
            
            # 2. 嘗試用 wave 模組讀取（方法1）
            print("嘗試用 wave 模組讀取...")
            sample_rate, audio_data = self.read_wav_with_wave_module(audio_filename)
            
            # 3. 如果 wave 模組失敗，用手動解析（方法2）
            if audio_data is None:
                print("wave 模組失敗，嘗試手動解析...")
                sample_rate, audio_data = self.read_wav_manual(audio_filename)
            
            # 4. 播放音檔
            if audio_data is not None:
                print(f"準備播放: {sample_rate}Hz, 形狀: {audio_data.shape}")
                sd.play(audio_data, samplerate=sample_rate, device=self.output_index)
                sd.wait()
                print("✅ 播放完成")
            else:
                print("❌ 無法讀取音檔")
                
        except Exception as e:
            print(f"錯誤: {e}")

    def test_tts(self):
        """測試功能"""
        self.speak("Hello, this is a test message.")