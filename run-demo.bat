@echo off
REM Mock 모드 실행 — LLM 호출 없이 즉시 응답
set LLM_BACKEND=mock
set MOCK_NO_DELAY=1
streamlit run app.py
