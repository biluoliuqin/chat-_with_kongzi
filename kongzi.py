import sys
import os
import random
import json
import tempfile
from pathlib import Path
import cv2
import numpy as np
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor
import pyaudio
import wave
import threading
import io
from glob import glob

from queue import Queue

# 媒体队列管理器
class MediaQueueManager:
    def __init__(self):
        self.video_queue = Queue(maxsize=10)
        self.audio_queue = Queue(maxsize=10)
        self.is_playing_video = False
        self.is_playing_audio = False
    
    def add_video(self, video_path):
        self.video_queue.put(video_path)
        
    def add_audio(self, audio_data):
        self.audio_queue.put(audio_data)
        
    def has_next_video(self):
        return not self.video_queue.empty()
        
    def has_next_audio(self):
        return not self.audio_queue.empty()
        
    def get_next_video(self):
        if not self.video_queue.empty():
            return self.video_queue.get()
        return None
        
    def get_next_audio(self):
        if not self.audio_queue.empty():
            return self.audio_queue.get()
        return None


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    video_ended_signal = pyqtSignal()

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self._run_flag = True
        

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                self.change_pixmap_signal.emit(frame)
                # 使用 QThread 的 msleep 而不是 time.sleep
                QThread.msleep(33)  # 约30fps
            else:
                self.video_ended_signal.emit()
                break
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("尊儒智道")
        # 设置窗口始终最大化
        self.showMaximized()
        
        # 媒体队列管理器
        self.media_queue = MediaQueueManager()
        
        # 状态变量
        self.is_recording = False
        self.is_prompting = False
        self.is_music_playing = False
        self.is_user_stopped = False
        self.messages = []
        self.last_video = None
        self.current_video_thread = None
        # 添加线程锁
        self.video_lock = threading.Lock()
        self.audio_lock = threading.Lock()
        
        # 音频相关
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.output_file = "recorded_audio.wav"        
        
        # 初始化UI
        self.init_ui()
        self.load_video_resources()
        self.play_random_video()
        self.play_background_music()
        
        # # 设置无边框窗口
        # self.setWindowFlags(Qt.FramelessWindowHint)
        
    def init_ui(self):
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 使用垂直布局作为主布局
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建一个widget作为视频和按钮的容器
        container = QWidget()
        container.setLayout(QVBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)
        container.layout().setSpacing(0)
        
        # 视频显示标签
        self.video_label = QLabel()
        # 设置视频标签的大小策略为扩展
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setAlignment(Qt.AlignCenter)
        container.layout().addWidget(self.video_label)
        
       # 创建按钮容器
        button_container = QWidget()
        button_container.setMaximumHeight(100)  # 增加按钮容器高度
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(20)  # 增加按钮之间的间隔
        
        # 录音按钮
        self.record_button = QPushButton("开始录音")
        self.record_button.setFixedSize(225, 90)  # 增大按钮尺寸
        self.record_button.clicked.connect(self.record_button_clicked)
        
        # 音乐按钮
        self.music_button = QPushButton("播放音乐")
        self.music_button.setFixedSize(225, 90)  # 增大按钮尺寸
        self.music_button.clicked.connect(self.music_button_clicked)
        
        # 添加弹性空间，使按钮居中对齐
        button_layout.addStretch()  # 在按钮前添加弹性空间
        button_layout.addWidget(self.record_button)
        button_layout.addWidget(self.music_button)
        button_layout.addStretch()  # 在按钮后添加弹性空间
        
        # 将按钮容器设置为浮动在视频下方
        button_container.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0);  /* 全透明背景 */
            }
            QPushButton {
                background-color: #8B4513;  /* 棕色背景 */
                color: #FFD700;  /* 金色文字 */
                border: 2px solid #DAA520;  /* 金色边框 */
                border-radius: 15px;  /* 增大圆角 */
                padding: 10px;  /* 增大内边距 */
                font-family: "KaiTi";  /* 使用楷体 */
                font-size: 36px;  /* 增大字体 */
            }
            QPushButton:hover {
                background-color: #A0522D;  /* 深棕色背景 */
            }
        """)
        
        # 创建一个QWidget作为按钮的覆盖层
        overlay = QWidget(container)
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addStretch()  # 将按钮推到底部
        overlay_layout.addWidget(button_container)
        
        # 设置覆盖层的大小策略
        overlay.setGeometry(0, 0, self.width(), self.height())
        container.installEventFilter(self)  # 安装事件过滤器以处理大小变化
        
        main_layout.addWidget(container)

    def closeEvent(self, event):
        try:
            # 停止所有线程和释放资源
            if self.current_video_thread is not None:
                self.current_video_thread.stop()
                self.current_video_thread.wait()
                
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop_stream()
                self.stream.close()
                
            if hasattr(self, 'audio') and self.audio:
                self.audio.terminate()
                
            if hasattr(self, 'background_player'):
                self.background_player.stop()
                
            # 清理临时文件
            if os.path.exists(self.output_file):
                try:
                    os.remove(self.output_file)
                except:
                    pass
        except Exception as e:
            print(f"关闭窗口错误: {e}")
        finally:
            event.accept()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            # 当容器大小改变时，更新覆盖层大小
            for child in obj.children():
                if isinstance(child, QWidget) and child != self.video_label:
                    child.setGeometry(0, 0, obj.width(), obj.height())
        return super().eventFilter(obj, event)

    def update_video_frame(self, frame):
        """更新视频帧，确保全屏显示"""
        try:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # 获取视频标签的实际大小
                label_size = self.video_label.size()
            
            # 缩放图像以填充整个标签，保持纵横比
                scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                    label_size,
                    Qt.KeepAspectRatioByExpanding,  # 改用KeepAspectRatioByExpanding
                    Qt.SmoothTransformation
                )
            
            # 如果缩放后的图像大于标签，裁剪居中部分
                if scaled_pixmap.width() > label_size.width() or scaled_pixmap.height() > label_size.height():
                    x = (scaled_pixmap.width() - label_size.width()) // 2 if scaled_pixmap.width() > label_size.width() else 0
                    y = (scaled_pixmap.height() - label_size.height()) // 2 if scaled_pixmap.height() > label_size.height() else 0
                    scaled_pixmap = scaled_pixmap.copy(
                        x, y, 
                        min(scaled_pixmap.width(), label_size.width()),
                        min(scaled_pixmap.height(), label_size.height())
                )    
            
                self.video_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"更新视频帧错误: {e}")
                
    def load_video_resources(self):
        video_dir = Path("videos")
        self.video_resources = list(video_dir.glob("*.mp4"))
        if not self.video_resources:
            print("错误: 未找到视频文件")
            
    def play_random_video(self):
        if not self.video_resources:
            return
            
        # 如果当前正在播放视频，则将新视频加入队列
        if self.media_queue.is_playing_video:
            available_videos = [v for v in self.video_resources if str(v) != self.last_video]
            if not available_videos:
                available_videos = self.video_resources
            video = random.choice(available_videos)
            self.media_queue.add_video(str(video))
            return
            
        # 开始播放视频
        self._play_next_video()
        
    def _play_next_video(self):
        try:
            # 停止当前视频线程
            if self.current_video_thread is not None:
                self.current_video_thread.stop()
                self.current_video_thread.wait()  # 等待线程结束
                self.current_video_thread.deleteLater()
        except Exception as e:
            print(f"停止视频线程错误: {e}")
        # 获取下一个要播放的视频
        video_path = self.media_queue.get_next_video()
        if not video_path:
            # 如果队列为空，随机选择一个视频
            available_videos = [v for v in self.video_resources if str(v) != self.last_video]
            if not available_videos:
                available_videos = self.video_resources
            video_path = str(random.choice(available_videos))
            
        self.last_video = video_path
        self.media_queue.is_playing_video = True
        
        # 创建新的视频线程
        self.current_video_thread = VideoThread(video_path)
        self.current_video_thread.change_pixmap_signal.connect(self.update_video_frame)
        self.current_video_thread.video_ended_signal.connect(self._handle_video_ended)
        self.current_video_thread.start()
        
    def _handle_video_ended(self):
        self.media_queue.is_playing_video = False
        if self.media_queue.has_next_video():
            self._play_next_video()
        else:
            self.play_random_video()

    def record_button_clicked(self):
        if self.is_recording:
            self.stop_recording()
        else:
            if self.is_prompting:
                print("警告: 请等待上一个对话完成")
                return
            else:
                self.is_prompting = True
                self.start_recording()

    def start_recording(self):
        # 降低背景音乐音量
        if self.is_music_playing:
            self.background_player.setVolume(30)

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        self.frames = []
        self.is_recording = True
        self.record_button.setText("停止录音")
        
        # 开始录音线程
        self.record_thread = threading.Thread(target=self.record_audio)
        self.record_thread.start()

    def record_audio(self):
        while self.is_recording:
            data = self.stream.read(self.CHUNK)
            self.frames.append(data)

    def stop_recording(self):
        self.is_recording = False
        self.record_button.setText("开始录音")
        
        # 恢复背景音乐音量
        if self.is_music_playing:
            self.background_player.setVolume(100)
        
        # 停止录音流
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        
        # 启动线程保存录音和转录
        threading.Thread(target=self.save_and_transcribe_audio).start()

    def save_and_transcribe_audio(self):
        try:
            with self.audio_lock:  # 使用锁保护音频操作
                with wave.open(self.output_file, 'wb') as wf:
                    wf.setnchannels(self.CHANNELS)
                    wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                    wf.setframerate(self.RATE)
                    wf.writeframes(b''.join(self.frames))
            
            # 清理资源
            self.frames = []
            self.transcribe_audio()
        except Exception as e:
            print(f"保存音频错误: {e}")
            self.is_prompting = False

    def transcribe_audio(self):
        try:
            with open(self.output_file, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    'https://3923-115-24-186-34.ngrok-free.app/v1/audio/transcriptions',
                    files=files
                )
                
            if response.status_code == 200:
                result = response.json()
                if 'text' in result:
                    self.messages.append({
                        'role': 'user',
                        'content': result['text']
                    })
                    # 显示转录结果
                    # print("转录结果:", result['text'])
                    self.send_chat_messages()
            else:
                print("错误: 转录失败")
                self.is_prompting = False
                
        except Exception as e:
            print(f"错误: 转录失败: {str(e)}")
            self.is_prompting = False

    def send_chat_messages(self):
        try:
            # 显示发送的内容
            sent_content = "\n".join([msg['content'] for msg in self.messages if msg['role'] == 'user'])
            # print("发送的内容:", sent_content)

            response = requests.post(
                'https://3923-115-24-186-34.ngrok-free.app/v1/chat/completions',
                json={'messages': self.messages}
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'message' in result:
                    message = result['message']
                    self.messages.append({
                        'role': message['role'],
                        'content': message['content']
                    })
                    # 每5轮对话左右触发一次视频,或匹配到了关键词
                    if len(self.messages) % 2 == 0 or any(keyword in message['content'] for keyword in ["教", "韦编三绝", "讲学", "琴", "肉味", "诗书", "鼓", "礼", "孝", "政", "穷", "水", "逝者如斯夫", "陈蔡", "颜回", "列国", "齐", "峡谷", "故事", "经历", "讲", "听", "传承", "道德", "智慧", "哲理", "修行", "师", "言","子","学生","仁","智"]):
                        
                        # 将self.messages发送到API
                        url = "https://3923-115-24-186-34.ngrok-free.app/dify"
                        params = {
                            "messages": json.dumps(self.messages)  # 使用json.dumps序列化整个消息列表
                        }
                        print("发送的内容:", params)
                        response = requests.post(url, params=params)
                        ans = response.json().get('ans', '')
                        print(ans)
                        # #先用Qchatbox显示ans
                        # print("对话结果:", ans)

                        # 根据ans结果插入对应视频
                        if ans:
                            video_paths = ans.split(", ")
                            for video_name in video_paths:
                                # 使用 glob 匹配所有符合前缀的文件
                                matched_videos = glob(f"historys/{video_name}*.mp4")
                                for video_path in matched_videos:
                                    if os.path.exists(video_path):
                                        self.media_queue.add_video(video_path)
                                    else:
                                        self.media_queue.add_video(r"historys\none.mp4")
                                    

                        # # 获取当前队列中的视频
                        # history_video = str(Path("historys/his1.mp4"))
                        # if os.path.exists(history_video):
                        #     # 然后添加his1视频
                        #     self.media_queue.add_video(history_video)
                    # print("接收的内容:", message['content'])
                    self.play_tts_audio(message['content'])
            else:
                print("错误: 对话请求失败")
                self.is_prompting = False
                
        except Exception as e:
            print(f"错误: 对话请求失败: {str(e)}")
            self.is_prompting = False

    def play_tts_audio(self, text):
        try:
            response = requests.get(
                f'https://3923-115-24-186-34.ngrok-free.app/v1/tts',
                params={'text': text},
                stream=True
            )
            if response.status_code == 200:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_audio_file_path = temp_file.name
                    print("临时文件保存在", temp_file.name)
                    
                    with wave.open(temp_file, 'wb') as wav_file:
                        # 设置WAV文件参数
                        wav_file.setnchannels(1)     # 单声道
                        wav_file.setsampwidth(2)     # 16位 = 2字节
                        wav_file.setframerate(32000) # 采样率32000Hz
                        
                        # 写入音频数据
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                wav_file.writeframes(chunk)


                # 降低背景音乐音量
                if self.is_music_playing:
                    self.background_player.setVolume(20)
                data = {
                "type": "speak",
                "speech_path": temp_audio_file_path
                }
                data = {
                    "type": "rhythm",
                    "music_path": temp_audio_file_path,
                    "beat": 1
                }

                def audio_callback():
                    try:
                        requests.post('http://127.0.0.1:7888/alive', json=data)
                    finally:
                        self.is_prompting = False
                        
                        # 恢复背景音乐音量
                        if self.is_music_playing:
                            self.background_player.setVolume(100)

                # 使用线程来播放音频
                threading.Thread(target=audio_callback).start()

            else:
                print("错误: TTS请求失败")
                self.is_prompting = False

        except Exception as e:
            print(f"错误: TTS请求失败: {str(e)}")
            self.is_prompting = False

    def handle_tts_finished(self, status, temp_file):
        if status == QMediaPlayer.EndOfMedia:
            # 删除临时文件
            os.unlink(temp_file)
            
            # 恢复背景音乐音量
            if self.is_music_playing:
                self.background_player.setVolume(100)
                
            self.is_prompting = False

    def play_background_music(self):
        if self.is_music_playing:
            return
            
        music_dir = Path("music")
        music_files = list(music_dir.glob("*.mp3"))
        
        if not music_files:
            return
            
        # 选择不重复的音乐并加入队列
        available_music = [m for m in music_files if str(m) != getattr(self, 'last_music', None)]
        if not available_music:
            available_music = music_files
            
        music_file = random.choice(available_music)
        self.last_music = str(music_file)
        
        # 将音乐文件添加到音频队列
        self.media_queue.add_audio(str(music_file))
        
        # 开始播放队列中的音乐
        self._play_next_music()
            
        self.background_player = QMediaPlayer()
        self.background_player.setMedia(
            QMediaContent(QUrl.fromLocalFile(str(music_file)))
        )
        self.background_player.mediaStatusChanged.connect(self.handle_music_finished)
        self.background_player.play()
        self.is_music_playing = True
        self.music_button.setText("停止音乐")

    def _play_next_music(self):
        # 获取队列中的下一个音乐
        music_path = self.media_queue.get_next_audio()
        if not music_path:
            return
            
        self.background_player = QMediaPlayer()
        self.background_player.setMedia(
            QMediaContent(QUrl.fromLocalFile(music_path))
        )
        self.background_player.mediaStatusChanged.connect(self.handle_music_finished)
        self.background_player.play()
        self.is_music_playing = True
        self.music_button.setText("停止音乐")
    
    def handle_music_finished(self, status):
        if status == QMediaPlayer.EndOfMedia and not self.is_user_stopped:
            if self.media_queue.has_next_audio():
                self._play_next_music()
            else:
                # 队列为空时重新添加新的音乐
                self.play_background_music()

    def music_button_clicked(self):
        if self.is_music_playing:
            self.is_user_stopped = True
            self.background_player.stop()
            self.is_music_playing = False
            self.music_button.setText("播放音乐")
            # 清空音频队列
            while self.media_queue.has_next_audio():
                self.media_queue.get_next_audio()
        else:
            self.is_user_stopped = False
            self.play_background_music()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            
    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos'):
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        
        # 设置应用程序样式
        app.setStyle('Fusion')
        
        # 创建暗色主题调色板
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        
        # 应用暗色主题
        app.setPalette(palette)
        
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"错误: {e}")
