import sys
import os
import time
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def run_seed():
    print("Инициализация и наполнение базы данных MySQL...")
    from database.connection import init_db
    from database.seed_data import seed_database
    init_db()
    seed_database()
    print("База данных готова.")


def run_api():
    print("Запуск FastAPI backend на http://127.0.0.1:8000 ...")
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)


def run_app():
    print("Запуск интерфейса Streamlit...")
    app_path = os.path.join(PROJECT_ROOT, "app", "streamlit_app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])


def run_tests():
    print("Запуск тестов...")
    test_path = os.path.join(PROJECT_ROOT, "tests", "test_recommenders.py")
    subprocess.run([sys.executable, test_path])


def run_all():
    run_seed()
    print("\nЗапуск FastAPI и Streamlit...")
    print("API Docs: http://127.0.0.1:8000/docs")
    print("Streamlit UI: http://localhost:8501\n")

    api_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"])
    time.sleep(2)

    try:
        app_path = os.path.join(PROJECT_ROOT, "app", "streamlit_app.py")
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
    finally:
        print("Остановка сервера API...")
        api_process.terminate()


if __name__ == "__main__":
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "help"

    if action == "seed":
        run_seed()
    elif action == "api":
        run_api()
    elif action == "app":
        run_app()
    elif action == "test":
        run_tests()
    elif action == "all":
        run_all()
    else:
        print("Использование: python run.py [seed|api|app|test|all]")
