# chat_with_kongzi

**chat_with_kongzi** 是一个结合现代人工智能技术与儒家文化的多模态互动平台，旨在通过技术复生孔子形象，帮助用户更加生动、深刻地理解儒家思想。本项目利用 **Live2D** 动态形象、**大语言模型**、语音识别与合成、文生视频等前沿技术，提供一个沉浸式的文化学习体验。

## 项目概述

本项目以孔子为核心，整合了人工智能的多种技术手段，打造了一个集 **虚拟人物**、**语音交互**、**视频重现** 于一体的儒家文化学习平台。通过与虚拟孔子的互动，用户可以学习儒家经典、听取孔子的智慧回答，并体验历史场景的再现，增强对儒家思想的理解和兴趣。

### 项目特点

1. **孔子 Live2D 形象**  
   利用 **Live2D** 技术，将孔子这一历史人物以动态的形象呈现。通过生成的孔子画像，用户不仅能够看到孔子的静态图像，还能够看到其微妙的面部表情变化、头部轻微转动、点头及手势动作。该 Live2D 模型的实现基于 EasyAIVtuber 仓库。
   EasyAIVtuber仓库地址：https://github.com/Ksuriuri/EasyAIVtuber
   基于儒家经典文献（如《四书五经》、《论语》、孔子生平等），本项目内置了一个由 **qwen2.5** 大语言模型提供支持的知识库，能够准确地以孔子的视角进行问答，提供深刻且符合历史背景的答案。  
   示例：  
   **用户问题**：孔子为何提出“仁”作为核心思想？  
   **模型回答**：孔子提出“仁”作为核心思想，是因为他认为“仁”是个人修养和社会和谐的基础……

3. **语音交互**  
   本项目实现了基于 **Whisper** 语音识别模型的语音输入功能，用户可以通过语音与孔子进行互动。通过 **GPT-SoVITS** 语音合成模型，系统会将孔子的回答转化为语音输出，形成真实的互动体验。

4. **历史场景重现（文生视频）**  
   本项目引入了 **文生视频（Text-to-Video）** 技术，能够根据用户提问生成相关的历史场景视频。用户在提问关于孔子或儒家学说的相关问题时，系统可以自动生成并播放相关的历史场景动画，增强学习的沉浸感和趣味性。

5. **PyQt 前端界面**  
   前端使用 **PyQt5** 实现，提供了一个简洁且直观的用户界面。用户可以通过该界面与孔子进行文本或语音的互动。为了提升用户体验，前端采用了多线程技术，确保界面响应流畅，后端计算任务得以高效执行。


## 功能介绍

### 1. **孔子 Live2D 形象展示**

- **Live2D** 技术用于展示孔子的动态形象，包括面部表情变化、头部转动、点头等动作，增强用户与孔子的互动感。
- 用户可以向孔子提问，孔子将通过适当的表情和肢体语言做出回应，提升互动体验。

### 2. **AI 大语言模型与知识库**

- 基于 **qwen2.5** 大语言模型，通过内置的儒家经典文献知识库，能够精准且深刻地回答关于孔子及儒家思想的各种问题。
- 知识库包含了大量的孔子生平、儒家经典以及儒家思想，确保回答准确且具有教育意义。

### 3. **语音交互**

- 通过 **Whisper** 模型实现语音识别，将用户语音转换为文本，并传入孔子语言模型进行处理。
- 通过 **GPT-SoVITS** 模型，将生成的回答转化为孔子的语音输出，用户可以通过语音与孔子对话。

### 4. **文生视频与历史场景重现**

- 结合 **Text-to-Video** 技术，自动生成与用户问题相关的历史场景视频。
- 例如，当用户询问孔子的生平或学说时，系统会生成孔子周游列国或杏坛讲学等经典历史场景的动画，增强学习的趣味性和沉浸感。

### 5. **前端界面与交互**

- **PyQt5** 用于构建简洁且易用的前端界面，支持文本输入、语音输入等多种交互方式。
- 采用多线程技术，确保前端界面响应迅速，不会因后台计算而卡顿。

## 环境依赖

### 后端依赖

- **大语言模型后端**: `ollama` 0.4.2  
  - **模型**: `qwen2.5:32b`
- **知识库后端**: `dify` 0.8.2
- **语音识别**: `whisper-large-v3`
- **TTS 模型**: `GPT-SoVITS V2`
- **文生视频生成**: `xinference` v0.15.0  
  - **嵌入模型**: `bge-large-zh-v1.5`  
  - **rerank 模型**: `bge-reranker-large`

### 前端依赖

- Python 3.10 及以上
- **孔子 Live2D 运行依赖**:
  - `torch>=2.3.1`
  - `torchvision>=0.18.1`
  - `torchaudio>=2.3.1`
- **前端依赖**:
  - `PyQt5`
  - `matplotlib`
  - `librosa`
  - `pygame`
  - `flask_restful`
  - `protobuf`
  - `pynput`
  - `mediapipe`
  - `opencv_python`
  - `Pillow`
  - `pyanime4k`
  - `pyvirtualcam`
  - `gradio`
  - `pyaudio`
  - `numpy`
  - `requests`

## 安装与运行

### 1. 安装依赖

在项目根目录下运行以下命令安装项目所需的 Python 依赖：
pip install -r requirements.txt


### 2. 启动后端

运行fastapi.py，启动后端 API 服务：

python fastapi.py

### 3. 启动前端

运行kongzi.py，启动前端界面：

python kongzi.py



贡献

我们欢迎社区对项目的贡献。如果您有任何想法、建议或问题，请通过 **GitHub Issues** 提交，或直接通过 **Pull Requests** 贡献代码。

### License

本项目采用 **None** 许可证，所有代码都可以自由使用和修改。

