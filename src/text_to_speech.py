import os
import sounddevice as sd
import soundfile as sf
import tempfile
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class TextToSpeech:
    def __init__(self, apikey, url):
        self.authenticator = IAMAuthenticator(apikey)
        self.text_to_speech = TextToSpeechV1(authenticator=self.authenticator)
        self.text_to_speech.set_service_url(url)
        self.output_device_index = None
        self._detect_audio_device()

    def _detect_audio_device(self):
        """自動偵測音頻輸出設備"""
        try:
            devices = sd.query_devices()
            print("搜尋音頻輸出設備...")
            
            # 尋找 USB Audio Device (喇叭/耳機)
            for i, device in enumerate(devices):
                if "USB Audio Device" in device['name'] and device['max_output_channels'] > 0:
                    self.output_device_index = i
                    print(f"找到播放設備: {device['name']} (index {i})")
                    return True
            
            # 如果沒找到 USB Audio，尋找其他可用的輸出設備
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:
                    self.output_device_index = i
                    print(f"使用備用播放設備: {device['name']} (index {i})")
                    return True
                    
            print("未找到可用的播放設備，將使用系統預設")
            self.output_device_index = None
            return False
            
        except Exception as e:
            print(f"播放設備偵測錯誤: {e}")
            self.output_device_index = None
            return False

    def speak(self, text):
        """使用 IBM Watson Text to Speech 將文字轉為語音並播放"""
        if not text or text.strip() == "":
            print("無效的文字輸入")
            return False
            
        try:
            print(f"正在轉換文字為語音: {text}")
            
            # 取得語音資料
            response = self.text_to_speech.synthesize(
                text,
                voice='en-US_AllisonV3Voice',  # 可以更改為其他聲音
                accept='audio/wav'
            ).get_result()

            # 使用臨時檔案
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_filename = temp_file.name

            print(f"音頻文件已生成: {temp_filename}")
            
            # 使用 sounddevice 播放
            success = self._play_audio_file(temp_filename)
            
            # 清理臨時檔案
            try:
                os.unlink(temp_filename)
            except:
                pass
                
            return success
            
        except Exception as e:
            print(f"文字轉語音錯誤: {e}")
            return False

    def _play_audio_file(self, filename):
        """使用 sounddevice 播放音頻檔案"""
        try:
            # 讀取音頻檔案
            data, samplerate = sf.read(filename)
            print(f"播放音頻 (採樣率: {samplerate}, 設備: {self.output_device_index})")
            
            # 播放音頻
            sd.play(data, samplerate=samplerate, device=self.output_device_index)
            sd.wait()  # 等待播放完成
            
            print("音頻播放完成")
            return True
            
        except Exception as e:
            print(f"音頻播放錯誤: {e}")
            # 如果 sounddevice 失敗，嘗試使用系統命令
            return self._fallback_play(filename)

    def _fallback_play(self, filename):
        """備用播放方法 - 使用系統命令"""
        try:
            print("嘗試使用系統命令播放...")
            
            # 嘗試不同的播放命令
            play_commands = [
                f"aplay -D plughw:3,0 {filename}",  # 原始方法
                f"aplay {filename}",  # 簡化版本
                f"paplay {filename}",  # PulseAudio
                f"sox {filename} -d",  # Sox
            ]
            
            for cmd in play_commands:
                try:
                    result = os.system(cmd)
                    if result == 0:
                        print(f"使用命令播放成功: {cmd}")
                        return True
                except:
                    continue
                    
            print("所有播放方法都失敗了")
            return False
            
        except Exception as e:
            print(f"備用播放方法錯誤: {e}")
            return False

    def test_speak(self):
        """測試語音輸出"""
        return self.speak("Hello, this is a test of the text to speech system.")