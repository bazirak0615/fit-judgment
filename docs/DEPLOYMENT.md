# 배포 가이드

## Streamlit Cloud (무료, 추천)

### 사전 준비
1. 깃헙 저장소 push 완료
2. https://share.streamlit.io 가입 (깃헙 계정으로 로그인)

### 배포 단계
1. Streamlit Cloud → "New app" 클릭
2. 저장소 선택, branch=main, main file=`app.py`
3. **Advanced settings** 클릭
4. **Secrets** 탭에 추가:
   ```toml
   LLM_BACKEND = "mock"
   ```
5. **Python version**: 3.12 선택
6. **Deploy** 클릭

### 배포 후
- 약 3~5분 후 라이브 URL 확인 (`https://xxx.streamlit.app`)
- 깃헙에 push할 때마다 자동 재배포

### 주의사항
- Streamlit Cloud 무료 티어는 1GB RAM, CPU 제한
- Mock 모드 권장 (실제 LLM 호출 시 느려짐)
- 실제 LLM 사용 시 secrets에 API 키 추가 필요
- SQLite 파일은 재배포 시 초기화됨 (영속 저장 필요 시 외부 DB)

---

## 로컬 시연 (Mock 모드, 즉시 응답)

```bash
LLM_BACKEND=mock MOCK_NO_DELAY=1 streamlit run app.py
```

`MOCK_NO_DELAY=1`을 추가하면 Mock 응답이 즉시 반환되어 시연 시 대기 시간 0.

---

## Docker 배포 (선택)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV LLM_BACKEND=mock
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t fit-evaluator .
docker run -p 8501:8501 fit-evaluator
```

---

## 깃헙에 push하기 전 점검

```bash
# 1. 민감 정보가 들어가지 않았는지
git diff --check
git ls-files | xargs grep -l "sk-" 2>/dev/null  # API 키 누락 검사
git ls-files | xargs grep -l "@.*\.com" 2>/dev/null  # 실제 이메일 검사

# 2. 데이터 디렉토리는 gitignore 확인
git status --ignored | head

# 3. Mock 데이터에 실제 후보자 정보가 없는지
ls mocks/candidates/  # 가공된 더미만 있어야 함

# 4. requirements 정리
pip freeze > requirements-lock.txt  # 참고용 (커밋은 requirements.txt만)
```
