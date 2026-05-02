# 🎯 적합인재 판단기 (JD-Resume Fit Evaluator)

> **JD와 후보자 이력서의 적합도를 7개 차원·정량 점수·근거 기반 narrative로 산출하고,
> 면접 질문 가이드와 PDF 보고서까지 자동 생성하는 채용 의사결정 보조 도구**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39+-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 핵심 가치

채용 담당자가 매번 반복하는 "이 후보자가 이 JD에 얼마나 맞는가?"라는 판단을
**일관된 정량 기준**으로 자동화합니다.

| 기존 채용 검토 | 본 시스템 |
|---|---|
| 평가자별 편차 큼 | 동일 가중치·기준 적용 — 일관 |
| 13명 검토에 1~2일 | 13명 일괄 평가 5분 (API 백엔드 기준) |
| 점수 + 한 줄 코멘트 | 차원별 점수 + 매칭/부족/근거 + 면접 질문 |
| Excel·PPT 수기 | PDF 보고서 자동 생성 |

---

## 동작 모드

> Mock 모드(기본값)는 사전 정의된 JD 3종 × 후보자 12명 시나리오로 LLM 호출 없이 동작합니다.
> 실제 운영 시에는 환경변수 한 줄로 Anthropic Claude / OpenAI GPT / 로컬 Ollama로 전환 가능합니다.

```
[Step 1] JD 입력 → LLM이 직무·필수요건·우대사항·강조키워드 자동 구조화
[Step 2] 가중치 조정 → AI 추천 + 차원별 JD 기준 토글로 직관적 조정
[Step 3] 후보자 일괄 평가 → 한 번에 1~100명, 후보자별 차원 점수 산출
[Step 4] 풍부한 보고서 → 후보자 카드 + 레이더차트 + 추천 사유 narrative
                      + 면접 질문 가이드 + PDF/CSV/JSON export
```

---

## 빠른 시작 (3분)

```bash
# 1. 클론
git clone <repo-url>
cd 17-fit-judgment

# 2. 의존성 설치
pip install -r requirements.txt

# 3. Mock 모드로 실행 (LLM 호출 없이 즉시 시연 가능)
#    macOS / Linux
LLM_BACKEND=mock streamlit run app.py    # 또는 ./run-demo.sh
#    Windows
#    run-demo.bat
```

브라우저: http://localhost:8501

**처음 사용자**:
1. `mocks/jds/education_lead.txt` 내용 복사 → JD 입력란에 붙여넣기 → "JD 구조화 →"
2. AI 추천 가중치 적용
3. `mocks/candidates/` 폴더의 4개 파일 동시 업로드 → "일괄 평가 시작"
4. **약 5초 후** Step 4 풍부한 리포트 확인

---

## 아키텍처

```
사용자
  ↓
Streamlit UI (app.py)
  ↓
src/engine/        # JD/이력서 추출 + 평가 매처
  ↓ generate_json()
src/llm/client.py  # 백엔드 라우팅
  ├→ src/llm/mock_backend.py    [LLM_BACKEND=mock]   ← 기본값 (LLM 없이 동작)
  ├→ src/llm/ (ollama)          [LLM_BACKEND=ollama] ← 로컬 운영
  └→ Anthropic/OpenAI API       [LLM_BACKEND=...]    ← 향후 확장
  ↓
src/db/store.py    # SQLite (평가 이력 + 가중치 프리셋)
  ↓
src/report/        # 차트(plotly) + narrative + PDF(reportlab)
```

### 핵심 설계 원칙

1. **LLM 백엔드 추상화** — `LLM_BACKEND` 환경변수 한 줄로 mock / ollama / API 전환
2. **결과 영속화** — 평가 1건 끝날 때마다 SQLite 저장, 새로고침해도 안전
3. **세션 자동 저장/복원** — `data/last_session.json`으로 작업 중단·재개 가능
4. **차원·가중치 분리** — 평가 차원·가중치·하드 게이트를 시스템화, JD별 프리셋 저장
5. **Mock 데이터로 즉시 동작** — API 키 없이도 클론 직후 전체 흐름 확인 가능

---

## 평가 차원 (기본 5개, 사용자 추가 가능)

| 차원 | 분류 | 기본 가중치 | 평가하는 것 |
|---|---|---|---|
| Hard Skills | 필수 | 30% | JD가 명시한 자격·스킬을 보유했는지 |
| Experience | 필수 | 25% | JD가 요구하는 업무를 실제로 해봤는지 |
| Achievements | 필수 | 20% | JD가 강조·암시한 성과 신호에 부합하는지 |
| Domain Fit | 우대 | 15% | 산업/도메인 배경이 맞는지 |
| Seniority | 우대 | 10% | 연차·역할 레벨이 맞는지 |

제약: 필수 합계 ≥ 50%, 우대 합계 ≤ 50%, 전체 = 100%.

---

## Mock 시나리오

3개 JD × 12명 후보자 = 12개 사전 작성 평가 (다른 조합은 휴리스틱 fallback)

| JD | 후보자 풀 (이상적) | 적합도 분포 |
|---|---|---|
| 교육사업팀장 (EduGrowth) | c01~c04 | 92 / 86 / 62 / 28 |
| 시니어 데이터 엔지니어 (DataPlex) | c05~c08 | 95 / 90 / 50 / 25 |
| 그로스 마케터 (SaaSlift) | c09~c12 | 96 / 89 / 65 / 30 |

각 평가에는 차원별 점수·매칭/부족 항목·근거 인용·검증 포인트·강점/리스크·면접 질문이 포함됩니다.

---

## 실제 운영 — LLM 백엔드 전환

Mock 모드는 데모용입니다. 실제 채용 평가에는 LLM 연동 필수:

### Option 1. Anthropic Claude API (권장)

```bash
# 향후 출시 예정 — src/llm/anthropic_client.py 추가 시
export ANTHROPIC_API_KEY=...
export LLM_BACKEND=anthropic
streamlit run app.py
```

- **속도**: 후보자 1명당 약 15~30초
- **비용**: Claude Haiku 4.5 기준 후보자 1명 약 100~200원
- **정확도**: Mock 데이터에 작성한 수준의 풍부한 결과를 실제로 산출

### Option 2. 로컬 Ollama (무료, CPU 추론)

```bash
ollama pull qwen2.5:7b
export LLM_BACKEND=ollama
streamlit run app.py
```

- **속도**: 후보자 1명당 5~30분 (CPU 환경)
- **비용**: 0원
- **추천**: 데이터 외부 전송 불가 환경 + 시간 여유 있을 때

---

## 폴더 구조

```
17. 적합인재 판단/
├── app.py                          # Streamlit 진입점
├── requirements.txt
├── README.md
│
├── src/
│   ├── engine/                     # JD/후보자 구조화 + 평가 로직
│   │   ├── extractor.py
│   │   ├── matcher.py
│   │   └── schema.py               # Dimension, Weights, HardGates
│   ├── llm/
│   │   ├── client.py               # 백엔드 라우팅 + Ollama 클라이언트
│   │   └── mock_backend.py         # 데모용 Mock LLM
│   ├── weights/                    # 가중치 추천 + 리밸런싱
│   ├── db/store.py                 # SQLite (평가 이력, 프리셋)
│   ├── parsers/                    # PDF/Word/Excel/JSON 파싱
│   └── report/                     # 차트 + narrative + PDF
│       ├── charts.py               # 레이더, 막대 (plotly)
│       ├── narrative.py            # 추천 사유, 면접 질문, 비교 요약
│       └── pdf_generator.py        # ReportLab PDF (한글 폰트 자동 탐색)
│
├── prompts/                        # LLM 프롬프트 템플릿 (4종)
│   ├── jd_extract.txt
│   ├── candidate_extract.txt
│   ├── dimension_eval.txt
│   └── weight_recommend.txt
│
├── mocks/                          # 데모 데이터 (시나리오 + 평가 결과)
│   ├── jds/                        # JD 본문 텍스트 3종
│   ├── candidates/                 # 후보자 이력서 12명
│   ├── fixtures.py                 # 시나리오 + 구조화 데이터
│   └── evaluations.py              # 사전 작성 평가 결과 12개
│
└── data/                           # 런타임 산출 (gitignore)
    ├── app.db                      # SQLite
    ├── last_session.json           # 세션 자동 저장
    └── llm_debug/                  # JSON 파싱 실패 시 raw 응답 보존
```

---

## 주요 기술 스택

| 레이어 | 기술 |
|---|---|
| Frontend | Streamlit 1.39+ |
| 시각화 | Plotly (레이더 / 막대 / 랭킹 차트) |
| LLM | Ollama (로컬), Mock (데모), Anthropic/OpenAI 확장 가능 |
| 저장 | SQLite |
| 보고서 | ReportLab (PDF), pandas (CSV) |
| 파일 파싱 | pdfplumber, python-docx, openpyxl |

---

## 연관 프로젝트

이 도구는 **JD 생성기**와 한 사이클로 동작합니다:

```
[16번] JD 자동 생성기  →  [17번] 적합인재 판단기
회사명 입력 → JD 자동 작성    JD + 이력서 → 적합도 평가
```

JD 작성부터 후보자 평가까지 채용 프로세스를 end-to-end 자동화.

---

## 한계와 향후 계획

### 현재 한계
- Mock 모드는 사전 정의 12명에서 풍부한 결과, 그 외 입력은 휴리스틱 fallback
- 실제 LLM 연동(Ollama)은 CPU 추론 시 매우 느림 — API 권장
- 한글 PDF는 Windows MalgunGothic 또는 Linux NanumGothic 자동 탐색

### 로드맵
- [ ] Anthropic Claude API 클라이언트 (`src/llm/anthropic_client.py`)
- [ ] OpenAI GPT API 클라이언트
- [ ] 평가 결과 vs 실제 채용 결과 정확도 검증 모듈
- [ ] Streamlit Cloud 라이브 데모 배포
- [ ] 후보자 평가 비교 차트 (스파이더 오버레이)

---

## 라이선스

MIT License. 자유롭게 포크·수정해 사용하세요.

`mocks/` 하위의 후보자 12명·JD 3종은 모두 가공된 가상 데이터로, 실제 인물·기업과 무관합니다.
