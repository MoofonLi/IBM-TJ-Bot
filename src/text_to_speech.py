import os
import struct
import sounddevice as sd
import scipy.io.wavfile as wavfile
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

    def fix_wav_header_inplace(self, filename):
        """直接在原檔案上修復 WAV header"""
        try:
            # 獲取檔案大小
            file_size = os.path.getsize(filename)
            correct_chunk_size = file_size - 8
            
            # 以讀寫模式打開檔案
            with open(filename, 'r+b') as f:
                # 檢查是否為 RIFF WAV
                f.seek(0)
                riff_header = f.read(4)
                if riff_header != b'RIFF':
                    print("不是 WAV 檔案")
                    return False
                
                # 讀取當前的檔案大小欄位
                current_size = struct.unpack('<I', f.read(4))[0]
                
                # 如果檔案大小欄位是 0xFFFFFFFF，就修復它
                if current_size == 0xFFFFFFFF:
                    print(f"檢測到損壞的檔案大小欄位: {hex(current_size)}")
                    print(f"修復為正確大小: {correct_chunk_size}")
                    
                    # 回到檔案大小欄位位置
                    f.seek(4)
                    # 寫入正確的檔案大小
                    f.write(struct.pack('<I', correct_chunk_size))
                    
                    print("✅ WAV header 已修復")
                    return True
                else:
                    print(f"檔案大小欄位正常: {current_size}")
                    return True
                    
        except Exception as e:
            print(f"修復失敗: {e}")
            return False

    def speak(self, text):
        """生成語音並播放"""
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
            
            # 2. 直接修復檔案開頭
            print("檢查並修復 WAV header...")
            self.fix_wav_header_inplace(audio_filename)
            
            # 3. 現在應該可以正常用 scipy 讀取了
            print("讀取修復後的音檔...")
            fs, data = wavfile.read(audio_filename)
            
            print(f"✅ 讀取成功 - 採樣率: {fs}Hz, 形狀: {data.shape}")
            
            # 4. 播放
            print("開始播放...")
            sd.play(data, samplerate=fs, device=self.output_index)
            sd.wait()
            print("播放完成")
            
        except Exception as e:
            print(f"錯誤: {e}")

    def test_tts(self):
        """測試功能"""
        self.speak("Hello, this is a test message.")