# 校园课程表智能助手 (Smart Schedule Reminder)

这是一个基于 Python 和 Streamlit 开发的校园生活效率工具，旨在解决学生容易忘记上课时间或地点的痛点。

## 🌐 在线演示
**[点击这里访问在线版](https://your-app-url.streamlit.app)** (请在部署后替换此链接)

## ✨ 功能特点

1.  **智能提醒**：实时显示当前状态（上课/空闲）及下一节课的倒计时。
2.  **自然语言查询**：支持模糊搜索，如“明天有什么课”、“高数在哪上”。
3.  **可视化课表**：直观展示每周课程安排。
4.  **数据管理**：支持 CSV 格式课表导入。

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.8+。

```bash
# 进入项目目录
cd smart_schedule_reminder

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行应用
双击运行目录下的 `run.bat` 脚本即可一键启动。

或者手动运行：
```bash
streamlit run app.py
```

## 📂 文件结构
- `app.py`: 主程序代码
- `schedule_data.csv`: 课程表数据源
- `requirements.txt`: 项目依赖库
- `run.bat`: 一键启动脚本

## 📝 自定义课表
您可以直接编辑 `schedule_data.csv` 文件，或在应用侧边栏上传新的 CSV 文件。CSV 格式需包含以下列：
`day, period, start_time, end_time, course_name, location, teacher`
