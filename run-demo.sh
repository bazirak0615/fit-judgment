#!/usr/bin/env bash
# Mock 모드 실행 — LLM 호출 없이 즉시 응답 (Linux/Mac)
export LLM_BACKEND=mock
export MOCK_NO_DELAY=1
streamlit run app.py
