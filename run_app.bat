@echo off
echo 데이터 스토리텔러 애플리케이션을 시작합니다...
echo.
echo 필요한 패키지가 설치되어 있는지 확인합니다.
pip install -r requirements.txt
echo.
echo 애플리케이션을 실행합니다.
streamlit run app.py
