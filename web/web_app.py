# gradio_app.py
import gradio as gr
import requests
from fastapi import HTTPException

# --- 配置 ---
# 定义 FastAPI 服务的内部地址（因为 Gradio 和 FastAPI 运行在同一进程中）
# 注意：这里使用 'http://127.0.0.1:8000' 是因为我们将从 Gradio 内部调用本地 FastAPI 服务
# 在生产或更复杂部署中，可能需要更健壮的服务发现机制
INTERNAL_API_URL = "http://127.0.0.1:8000"
SAY_HELLO_ENDPOINT = "/greetings/sayhello"
FULL_API_URL = f"{INTERNAL_API_URL}{SAY_HELLO_ENDPOINT}"
# --- 配置结束 ---

def call_say_hello_from_gradio():
    """
    Gradio 界面用来调用 FastAPI /greetings/sayhello 端点的函数。
    这个函数运行在 Gradio 服务器进程中，因此可以直接调用本地的 FastAPI 服务。
    """
    try:
        # 发送 HTTP GET 请求到 FastAPI 服务
        response = requests.get(FULL_API_URL)
        
        # 检查 HTTP 状态码
        response.raise_for_status() 
        
        # 解析 JSON 响应
        data = response.json()
        
        # 返回消息内容
        return data.get("message", "Received response but no 'message' field found.")
    
    except requests.exceptions.ConnectionError:
        # 处理无法连接到 API 的情况 (例如，FastAPI 未启动)
        error_msg = "无法连接到后端 API 服务，请检查服务是否正在运行。"
        print(f"[Gradio Error] {error_msg}") # 服务器端日志
        # 向 Gradio 用户界面返回错误信息
        return error_msg
        
    except requests.exceptions.HTTPError as e:
        # 处理 HTTP 错误 (例如 4xx, 5xx)
        status_code = e.response.status_code
        error_detail = e.response.text
        error_msg = f"API 调用失败 (HTTP {status_code}): {error_detail}"
        print(f"[Gradio Error] {error_msg}")
        return error_msg
        
    except requests.exceptions.RequestException as e:
        # 处理其他 requests 相关的错误
        error_msg = f"请求过程中发生错误: {e}"
        print(f"[Gradio Error] {error_msg}")
        return error_msg
        
    except Exception as e:
        # 处理其他未预期的错误
        error_msg = f"发生未知错误: {e}"
        print(f"[Gradio Error] {error_msg}")
        return error_msg


# --- 定义 Gradio Blocks 界面 ---
with gr.Blocks(title="PC Agent Client (Integrated)") as demo:
    gr.Markdown("## 🤖 PC Agent Interaction Demo (Integrated with FastAPI)")
    gr.Markdown("This UI is served by the same FastAPI process!")
    
    with gr.Row():
        btn_hello = gr.Button("👋 Say Hello to PC Agent!", variant="primary") # 添加样式
    
    with gr.Row():
        output_text = gr.Textbox(
            label="🤖 Response from PC Agent",
            placeholder="Click the button above...",
            interactive=False,
            lines=3 # 增加显示行数
        )

    # 绑定按钮点击事件到函数
    btn_hello.click(
        fn=call_say_hello_from_gradio,
        inputs=None, # 此函数不需要输入参数
        outputs=output_text # 输出到 textbox
    )
    
    # 可以添加更多组件和交互...

# 关键点：我们创建了 Gradio Blocks 对象 `demo`，但没有调用 launch()

# 导出 Gradio 应用实例，以便在 main.py 中挂载
# Gradio 的 Blocks 对象可以直接作为 ASGI 应用使用
gradio_app = demo