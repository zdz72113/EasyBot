"""
EasyBot v2.0 启动脚本
同时启动 FastAPI 后端和 Vue3 前端
"""
import subprocess
import sys
import os
import time
import signal
from pathlib import Path


def run_backend():
    """启动后端服务"""
    print("🚀 启动 FastAPI 后端服务...")
    root_dir = Path(__file__).parent
    
    # 检查依赖
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("📦 安装后端依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "app/requirements.txt"], 
                      cwd=str(root_dir))
    
    # 启动服务（从根目录运行，使用 app.main）
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
        cwd=str(root_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    return proc


def run_frontend():
    """启动前端服务"""
    print("🚀 启动 Vue3 前端服务...")
    web_dir = Path(__file__).parent / "app" / "web"
    
    # 检查 node_modules
    if not (web_dir / "node_modules").exists():
        print("📦 安装前端依赖...")
        subprocess.run(["npm", "install"], cwd=str(web_dir), shell=True)
    
    # 启动服务
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(web_dir),
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    return proc


def main():
    """主函数"""
    print("=" * 60)
    print("🧠 EasyBot v2.0 - 知识创作工作台")
    print("=" * 60)
    
    # 启动后端
    backend_proc = run_backend()
    time.sleep(2)  # 等待后端启动
    
    # 启动前端
    frontend_proc = run_frontend()
    time.sleep(2)  # 等待前端启动
    
    print("\n" + "=" * 60)
    print("✅ 服务已启动!")
    print("   后端 API: http://localhost:8000")
    print("   前端界面: http://localhost:5173")
    print("   API 文档: http://localhost:8000/docs")
    print("=" * 60)
    print("\n按 Ctrl+C 停止所有服务\n")
    
    # 等待中断
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("👋 已退出")


if __name__ == "__main__":
    main()
