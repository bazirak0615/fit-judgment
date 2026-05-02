# 17. 적합인재 판단 — Docs

본 폴더는 프로젝트 관련 문서·기획안·배포 가이드를 보관한다.

## 구조

```
docs/
├── README.md                 # 본 문서 (인덱스)
├── PRD.md                    # ★ 기획안 / V1 → V2 변경 로그 (최신)
└── DEPLOYMENT.md             # 배포 가이드 (Streamlit Cloud / Docker)
```

## 주요 문서

- **[PRD.md](PRD.md)** — V1(운영용 MVP) → V2(공개 데모 모드) 기획·변경 로그. V2에서 추가된 17개 기능(V2-A ~ V2-Q) 정리.
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Streamlit Cloud / Docker / 깃헙 push 점검 가이드.

## 참고

- 본 도구는 별도의 JD 생성기 프로젝트와 한 사이클로 동작합니다 (JD 생성 → 후보자 적합도 평가).
- 두 도구의 연동 시나리오는 [PRD.md §12](PRD.md) 참조.
