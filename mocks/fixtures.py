"""사전 정의된 데모 데이터.

3개 JD 시나리오 × 12명 후보자 풀 = 결정적 평가 결과.
시연 시 사용자가 mocks/jds/*.txt와 mocks/candidates/*.txt를 그대로 업로드하면
사전 작성된 풍부한 결과를 즉시 받을 수 있도록 설계됨.
"""
from pathlib import Path
from typing import Any

MOCKS_DIR = Path(__file__).resolve().parent
JDS_DIR = MOCKS_DIR / "jds"
CANDIDATES_DIR = MOCKS_DIR / "candidates"


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ============================================================
#  JD 시나리오 — 본문 + 구조화 결과 + 가중치 추천
# ============================================================

JD_SCENARIOS: dict[str, dict[str, Any]] = {
    "education_lead": {
        "id": "education_lead",
        "label": "교육사업팀장 (EduGrowth)",
        "match_keywords": ["교육사업", "교육사업팀장", "edugrowth", "퍼널 전환율", "완강률", "재구매율", "상품기획 파트", "교육운영 파트", "유니브"],
        "jd_text": _read_txt(JDS_DIR / "education_lead.txt"),
        "structured": {
            "position_title": "교육사업팀장",
            "company": "EduGrowth Inc.",
            "domain": ["에듀테크", "온라인 강의", "관리형 컨설팅", "입시·고등교육"],
            "seniority_level": "Lead",
            "must_have": [
                "7~9년 이상 경력 보유 · 리더 경험",
                "교육사업 기획 및 운영 경험 필수 (온라인 강의·컨설팅·학원·에듀테크 무관)",
                "복수 파트 또는 복수 직무 (기획+운영) 동시 관리 경험 3년 이상",
                "퍼널 지표·완강률·재구매율 등 교육 운영 지표를 직접 설계·개선한 경험",
                "마케팅·운영·CX 등 다른 팀과 얼라인하며 전체 퍼널을 굴려본 경험",
            ],
            "nice_to_have": [
                "입시·고등교육 도메인 경험",
                "온라인 강의 상품 또는 관리형 프로그램을 직접 기획·런칭한 경험",
                "외부 강사·컨설턴트 소싱·온보딩·QC 운영 경험",
                "에듀테크 스타트업 또는 빠른 성장기 조직 경험",
                "콘텐츠 마케팅·퍼포먼스 마케팅 협업 경험",
            ],
            "key_responsibilities": [
                "상품기획 파트와 교육운영 파트 두 파트 총괄",
                "퍼널 단계별 상품 전환율·완강률·재구매율 통합 모니터링",
                "마케팅·미디어·고객경험 파트와 크로스팀 협업 조율",
                "팀 KPI 설계 및 매출 목표 관리 (보수/기준/낙관 시나리오)",
                "팀원 채용·온보딩 주도",
            ],
            "hidden_criteria": [
                "히트 상품 1개 이상 직접 만든 경험",
                "콘텐츠 인지도를 결제로 전환한 퍼널 실행력",
                "고단가 B2C 서비스 신뢰 구조 설계 경험",
            ],
            "avoidance_signals": [
                "기획 또는 운영 한 가지만 해본 경력",
                "현장 없이 전략만 그리는 역할 선호",
                "안정된 프로세스만 선호",
            ],
            "emphasis_keywords": [
                {"keyword": "퍼널", "frequency": 8, "context": "전환율·매출 직결"},
                {"keyword": "완강률", "frequency": 4, "context": "교육 운영 KPI"},
                {"keyword": "재구매율", "frequency": 3, "context": "LTV 확장"},
                {"keyword": "기획+운영", "frequency": 5, "context": "복합 책임 강조"},
                {"keyword": "신뢰 구조", "frequency": 3, "context": "고단가 매출 핵심"},
            ],
        },
    },
    "data_engineer": {
        "id": "data_engineer",
        "label": "시니어 데이터 엔지니어 (DataPlex)",
        "match_keywords": ["데이터 엔지니어", "data engineer", "dataplex", "spark", "kafka", "airflow", "feature store", "etl"],
        "jd_text": _read_txt(JDS_DIR / "data_engineer.txt"),
        "structured": {
            "position_title": "시니어 데이터 엔지니어",
            "company": "DataPlex Inc.",
            "domain": ["데이터 인프라", "이커머스", "핀테크"],
            "seniority_level": "Senior",
            "must_have": [
                "데이터 엔지니어링 6년 이상 (백엔드 개발 포함 가능)",
                "Spark/Hadoop 등 분산 처리 프레임워크 운영 경험 3년 이상",
                "Python + SQL 능숙",
                "AWS/GCP 등 클라우드 환경에서의 데이터 인프라 구축 경험",
                "Airflow 또는 유사 워크플로우 오케스트레이션 운영 경험",
            ],
            "nice_to_have": [
                "핀테크/이커머스 도메인 경험",
                "Feature Store 또는 ML 인프라 구축 경험",
                "IaC (Terraform) 운영 경험",
                "Open source 기여 또는 컨퍼런스 발표 경험",
                "영어 비즈니스 회화",
                "비용 최적화로 인프라 비용 30%+ 절감 경험",
            ],
            "key_responsibilities": [
                "일 50억 건 이벤트 ETL 파이프라인 운영",
                "Kafka 기반 실시간 스트리밍 파이프라인 신규 구축",
                "Feature Store + 실시간 KPI 대시보드 백엔드 개발",
                "데이터 품질·신뢰성 보장 (SLA 99.9%)",
                "주니어 멘토링 + 아키텍처 결정 주도",
            ],
            "hidden_criteria": [
                "대규모 (일 1억 건 이상) 처리 경험",
                "비용 최적화 실적",
                "팀 멘토링 경험",
            ],
            "avoidance_signals": [
                "분석·BI 위주 경력 (인프라 직접 구축 미경험)",
                "단일 시스템·단일 회사 경력만 보유",
                "신규 제품 개발에 관심 없는 운영 위주",
            ],
            "emphasis_keywords": [
                {"keyword": "Spark", "frequency": 7, "context": "분산 처리 핵심"},
                {"keyword": "Kafka", "frequency": 5, "context": "스트리밍 신규 구축"},
                {"keyword": "Airflow", "frequency": 4, "context": "필수 오케스트레이션"},
                {"keyword": "비용 최적화", "frequency": 3, "context": "월 $80K → 30% 절감 목표"},
                {"keyword": "Feature Store", "frequency": 3, "context": "신규 데이터 제품"},
            ],
        },
    },
    "growth_marketer": {
        "id": "growth_marketer",
        "label": "그로스 마케터 (SaaSlift)",
        "match_keywords": ["그로스 마케터", "growth marketer", "saaslift", "라이프사이클", "퍼포먼스 마케팅", "braze", "a/b 테스트", "plg"],
        "jd_text": _read_txt(JDS_DIR / "growth_marketer.txt"),
        "structured": {
            "position_title": "그로스 마케터 (Performance + Lifecycle)",
            "company": "SaaSlift Inc.",
            "domain": ["B2B SaaS", "협업 도구", "PLG"],
            "seniority_level": "Mid-Senior",
            "must_have": [
                "디지털 마케팅 또는 그로스 5년 이상 경력",
                "유료 광고 직접 집행 (월 5천만원 이상 운영) 경험 2년 이상",
                "SQL 직접 쿼리 가능 (BI 분석가 도움 없이 대시보드 제작)",
                "A/B 테스트 설계·해석 경험",
                "라이프사이클 마케팅 도구 (Braze/Customer.io 등) 운영 경험",
            ],
            "nice_to_have": [
                "B2B SaaS 또는 PLG 모델 경험",
                "HubSpot/Marketo/Pardot 등 MA 도구 admin 경험",
                "Python으로 데이터 분석 자동화",
                "영어 비즈니스 회화 (글로벌 캠페인)",
                "Series B 이후 스타트업에서 그로스 팀 빌딩 경험",
            ],
            "key_responsibilities": [
                "Google/Meta/LinkedIn/Naver 광고 직접 집행, 월 광고비 5천→1.5억 확대",
                "라이프사이클 단계별 메일·인앱 메시지·리타게팅 설계",
                "월 5~10건 A/B 실험 운영, 분기 유의미 1~3건 발굴",
                "SQL 직접 쿼리 + Tableau/Looker 대시보드 제작",
                "프로덕트·세일즈·콘텐츠팀과 크로스팀 협업",
            ],
            "hidden_criteria": [
                "퍼포먼스 + 라이프사이클 통합 경험 (분리 X)",
                "PLG 모델 이해도",
                "데이터 분석 자체 수행 가능",
            ],
            "avoidance_signals": [
                "콘텐츠 마케팅·브랜딩 위주 경력 (퍼포먼스 직접 집행 미경험)",
                "광고 대행사 출신만 있고 인하우스 미경험",
                "SQL 안 다루는 분",
            ],
            "emphasis_keywords": [
                {"keyword": "퍼포먼스", "frequency": 6, "context": "직접 집행 강조"},
                {"keyword": "라이프사이클", "frequency": 5, "context": "Braze 운영"},
                {"keyword": "A/B 테스트", "frequency": 4, "context": "실험 문화"},
                {"keyword": "SQL", "frequency": 4, "context": "직접 분석 필수"},
                {"keyword": "PLG", "frequency": 3, "context": "B2B SaaS 성장 모델"},
            ],
        },
    },
}


# ============================================================
#  가중치 추천 — JD별 AI 추천 결과
# ============================================================

WEIGHT_RECOMMENDATIONS: dict[str, dict[str, Any]] = {
    "education_lead": {
        "adjustments": [
            {"dimension": "Hard Skills", "default": 0.30, "recommended": 0.30, "delta": 0.00,
             "reason": "필수 자격은 유지. 교육사업 기획·운영 경험이 명시적으로 강조됨"},
            {"dimension": "Experience", "default": 0.25, "recommended": 0.30, "delta": 0.05,
             "reason": "'기획+운영' 복합 책임이 emphasis_keywords로 5회 강조됨 (+5%)"},
            {"dimension": "Achievements", "default": 0.20, "recommended": 0.20, "delta": 0.00,
             "reason": "퍼널 지표·완강률 직접 개선 경험이 hidden_criteria로 명시"},
            {"dimension": "Domain Fit", "default": 0.15, "recommended": 0.10, "delta": -0.05,
             "reason": "입시·고등교육은 우대지만 필수 아님 (-5%)"},
            {"dimension": "Seniority", "default": 0.10, "recommended": 0.10, "delta": 0.00,
             "reason": "7~9년 + 리더 경험 명시 — 기본값 유지"},
        ],
        "final_weights": {"Hard Skills": 0.30, "Experience": 0.30, "Achievements": 0.20, "Domain Fit": 0.10, "Seniority": 0.10},
        "warnings": [],
    },
    "data_engineer": {
        "adjustments": [
            {"dimension": "Hard Skills", "default": 0.30, "recommended": 0.35, "delta": 0.05,
             "reason": "Spark/Kafka/Airflow 등 구체 기술 스택이 강하게 명시 (+5%)"},
            {"dimension": "Experience", "default": 0.25, "recommended": 0.25, "delta": 0.00,
             "reason": "6년 이상 경력 명시 — 기본값 유지"},
            {"dimension": "Achievements", "default": 0.20, "recommended": 0.20, "delta": 0.00,
             "reason": "비용 최적화 30%+ 같은 정량 목표 — 기본값 적정"},
            {"dimension": "Domain Fit", "default": 0.15, "recommended": 0.10, "delta": -0.05,
             "reason": "핀테크/이커머스는 우대 정도 (-5%)"},
            {"dimension": "Seniority", "default": 0.10, "recommended": 0.10, "delta": 0.00,
             "reason": "Senior 레벨 명시 — 기본값 유지"},
        ],
        "final_weights": {"Hard Skills": 0.35, "Experience": 0.25, "Achievements": 0.20, "Domain Fit": 0.10, "Seniority": 0.10},
        "warnings": [],
    },
    "growth_marketer": {
        "adjustments": [
            {"dimension": "Hard Skills", "default": 0.30, "recommended": 0.30, "delta": 0.00,
             "reason": "유료 광고 + SQL + A/B 테스트 등 다층 스킬 — 기본값 유지"},
            {"dimension": "Experience", "default": 0.25, "recommended": 0.30, "delta": 0.05,
             "reason": "퍼포먼스+라이프사이클 통합 경험이 hidden_criteria — 통합 경력 가중 (+5%)"},
            {"dimension": "Achievements", "default": 0.20, "recommended": 0.20, "delta": 0.00,
             "reason": "ROAS 개선·CAC 절감 등 정량 성과 — 기본값 유지"},
            {"dimension": "Domain Fit", "default": 0.15, "recommended": 0.15, "delta": 0.00,
             "reason": "B2B SaaS / PLG 도메인이 명시 우대 — 가중치 유지"},
            {"dimension": "Seniority", "default": 0.10, "recommended": 0.05, "delta": -0.05,
             "reason": "5년 이상이면 충분, 디렉터급은 아님 (-5%)"},
        ],
        "final_weights": {"Hard Skills": 0.30, "Experience": 0.30, "Achievements": 0.20, "Domain Fit": 0.15, "Seniority": 0.05},
        "warnings": [],
    },
}


# ============================================================
#  후보자 12명 — 본문 + 구조화 결과
# ============================================================

CANDIDATE_FIXTURES: dict[str, dict[str, Any]] = {
    "c01": {
        "id": "c01", "label": "정현우", "primary_jd": "education_lead",
        "match_keywords": ["정현우", "hyun-woo", "educore"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c01_education_strong.txt"),
        "structured": {
            "candidate_name": "정현우",
            "total_experience_years": 8,
            "current_title": "사업개발팀 리드 @ EduCore",
            "career_history": [
                {"company": "EduCore", "company_stage": "스타트업", "domain": ["에듀테크", "입시"], "title": "사업개발팀 리드", "duration_months": 38,
                 "responsibilities": ["입시 컨설팅+VOD 패키지 상품 기획·런칭·운영 총괄", "팀원 8명(기획4/운영4) 매니징"],
                 "achievements": [
                     {"action": "신규 관리형 상품 'EduCore PRO' 런칭", "result": "출시 6개월 누적 매출 38억"},
                     {"action": "단건 VOD → 패키지 업셀 구조 도입", "result": "객단가 +120%"},
                     {"action": "완강률 개선 (커뮤니티+1:1 멘토)", "result": "32% → 58%"},
                     {"action": "컨설팅 합격률", "result": "78% (업계 평균 55%)"},
                 ]},
                {"company": "Klassup", "company_stage": "스타트업", "domain": ["에듀테크", "입시"], "title": "상품기획 매니저", "duration_months": 33,
                 "responsibilities": ["온라인 입시 강의 상품 기획", "강사 소싱·QC"],
                 "achievements": [
                     {"action": "신규 강사 발굴", "result": "12명 중 3명이 회사 매출 30%"},
                     {"action": "외부 컨설턴트 SOP 문서화", "result": "8명 온보딩 완료"},
                     {"action": "학습 데이터 분석 → 커리큘럼 재설계", "result": "완강률 25% → 41%"},
                 ]},
                {"company": "EdAcademy", "company_stage": "중견", "domain": ["교육", "오프라인 학원"], "title": "운영 매니저", "duration_months": 28,
                 "responsibilities": ["오프라인 학원 → 온라인 전환 운영"],
                 "achievements": [
                     {"action": "수강생 확대", "result": "1,200 → 4,500명"},
                     {"action": "CS 응대 시간", "result": "18분 → 6분"},
                 ]},
            ],
            "skills": {
                "technical": ["SQL", "Mixpanel", "Notion", "Slack"],
                "domain": ["상품 기획", "교육 운영", "퍼널 설계", "강사 매니지먼트", "SOP 구축"],
                "language": [{"name": "영어", "level": "Business"}],
            },
            "leadership_signals": ["8명 팀 매니징", "외부 컨설턴트 8명 온보딩", "신규 상품 런칭 주도"],
            "stability_signals": {"shortest_tenure_months": 28, "longest_tenure_months": 38, "recent_3_avg_months": 33},
        },
    },
    "c02": {
        "id": "c02", "label": "박지윤", "primary_jd": "education_lead",
        "match_keywords": ["박지윤", "ji-yoon", "learnhub"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c02_education_mid.txt"),
        "structured": {
            "candidate_name": "박지윤",
            "total_experience_years": 6,
            "current_title": "마케팅·CRM 매니저 @ LearnHub",
            "career_history": [
                {"company": "LearnHub", "company_stage": "스타트업", "domain": ["에듀테크", "어학"], "title": "마케팅·CRM 매니저", "duration_months": 28,
                 "responsibilities": ["라이프사이클 캠페인 설계·운영 (Braze)", "리텐션 분석"],
                 "achievements": [
                     {"action": "재구매율 개선", "result": "12% → 24%"},
                     {"action": "신규 패키지 캠페인", "result": "ROAS 3.8"},
                 ]},
                {"company": "EnglishStream", "company_stage": "스타트업", "domain": ["에듀테크", "어학"], "title": "마케팅 매니저", "duration_months": 33,
                 "responsibilities": ["유료 광고 (Google/Meta) 월 3천만원 운영"],
                 "achievements": [
                     {"action": "CAC 절감", "result": "12만원 → 8만원"},
                     {"action": "신규 가입 확대", "result": "월 800 → 2,200건"},
                 ]},
                {"company": "EduTrend", "company_stage": "스타트업", "domain": ["교육"], "title": "마케팅 어소시에이트", "duration_months": 14,
                 "responsibilities": ["SNS 채널 운영", "인플루언서 협업"],
                 "achievements": [{"action": "인스타 팔로워", "result": "2K → 18K"}]},
            ],
            "skills": {
                "technical": ["SQL", "Mixpanel", "Braze"],
                "domain": ["라이프사이클 마케팅", "재구매 캠페인", "콘텐츠 마케팅", "SEO"],
                "language": [{"name": "영어", "level": "Conversational"}],
            },
            "leadership_signals": ["부서 시니어 (4명 중)"],
            "stability_signals": {"shortest_tenure_months": 14, "longest_tenure_months": 33, "recent_3_avg_months": 25},
        },
    },
    "c03": {
        "id": "c03", "label": "김도현", "primary_jd": "education_lead",
        "match_keywords": ["김도현", "do-hyun", "retailhub"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c03_education_weak.txt"),
        "structured": {
            "candidate_name": "김도현",
            "total_experience_years": 4,
            "current_title": "운영 매니저 @ RetailHub",
            "career_history": [
                {"company": "RetailHub", "company_stage": "스타트업", "domain": ["이커머스"], "title": "운영 매니저", "duration_months": 16,
                 "responsibilities": ["주문·CS·반품 운영"], "achievements": [{"action": "CS SLA 개선", "result": "24h → 6h"}]},
                {"company": "ShopFlow", "company_stage": "스타트업", "domain": ["이커머스"], "title": "CS 어소시에이트", "duration_months": 19,
                 "responsibilities": ["1:1 고객 응대"], "achievements": []},
                {"company": "CafeWorks", "company_stage": "중견", "domain": ["F&B"], "title": "매장 매니저", "duration_months": 17,
                 "responsibilities": ["카페 매장 운영"], "achievements": [{"action": "직원 매니징", "result": "5명"}]},
            ],
            "skills": {
                "technical": ["Excel", "Notion"],
                "domain": ["CS 운영", "운영 매뉴얼 작성"],
                "language": [{"name": "영어", "level": "미기재"}],
            },
            "leadership_signals": ["운영팀 3명 매니징"],
            "stability_signals": {"shortest_tenure_months": 16, "longest_tenure_months": 19, "recent_3_avg_months": 17},
        },
    },
    "c04": {
        "id": "c04", "label": "윤서연", "primary_jd": "education_lead",
        "match_keywords": ["윤서연", "seo-yeon", "classpath"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c04_education_strong2.txt"),
        "structured": {
            "candidate_name": "윤서연",
            "total_experience_years": 9,
            "current_title": "사업본부장 @ ClassPath",
            "career_history": [
                {"company": "ClassPath", "company_stage": "스타트업", "domain": ["에듀테크", "부트캠프"], "title": "사업본부장", "duration_months": 49,
                 "responsibilities": ["부트캠프 상품 기획+운영+강사 매니지먼트 총괄", "팀원 14명 통솔"],
                 "achievements": [
                     {"action": "연 매출 성장", "result": "80억 → 240억"},
                     {"action": "신규 코스 런칭", "result": "5개"},
                     {"action": "취업률", "result": "78%"},
                     {"action": "멤버십 모델 도입", "result": "MRR 4억"},
                 ]},
                {"company": "EduStarter", "company_stage": "스타트업", "domain": ["에듀테크"], "title": "콘텐츠 운영 리드", "duration_months": 35,
                 "responsibilities": ["온라인 강의 제작·운영"],
                 "achievements": [{"action": "신규 강의", "result": "60편, 누적 4만 명"}, {"action": "강사 NPS", "result": "65"}]},
                {"company": "Younivco", "company_stage": "스타트업", "domain": ["에듀테크", "입시"], "title": "학습 운영 매니저", "duration_months": 26,
                 "responsibilities": ["입시 컨설팅 운영"],
                 "achievements": [{"action": "합격률", "result": "71% (전년 +18%p)"}]},
            ],
            "skills": {
                "technical": ["SQL", "Mixpanel"],
                "domain": ["상품 기획+운영 통합", "강사 소싱·QC", "멤버십·구독 모델", "데이터 기반 운영"],
                "language": [{"name": "영어", "level": "Business"}],
            },
            "leadership_signals": ["14명 팀 통솔", "신규 코스 5개 런칭", "사업본부장"],
            "stability_signals": {"shortest_tenure_months": 26, "longest_tenure_months": 49, "recent_3_avg_months": 37},
        },
    },
    "c05": {
        "id": "c05", "label": "이상혁", "primary_jd": "data_engineer",
        "match_keywords": ["이상혁", "sang-hyuk", "paylink"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c05_data_strong.txt"),
        "structured": {
            "candidate_name": "이상혁",
            "total_experience_years": 8,
            "current_title": "시니어 데이터 엔지니어 @ PayLink",
            "career_history": [
                {"company": "PayLink", "company_stage": "스타트업", "domain": ["핀테크"], "title": "시니어 데이터 엔지니어", "duration_months": 30,
                 "responsibilities": ["일 60억 건 ETL", "Kafka+Flink 사기탐지", "Feature Store 도입", "주니어 3명 멘토링"],
                 "achievements": [
                     {"action": "사기 탐지 지연", "result": "800ms → 50ms"},
                     {"action": "AWS 비용 절감", "result": "$95K → $62K (35%)"},
                 ]},
                {"company": "CoinTrack", "company_stage": "스타트업", "domain": ["핀테크"], "title": "데이터 엔지니어", "duration_months": 33,
                 "responsibilities": ["일 8억 건 처리", "dbt 30+ 모델"],
                 "achievements": [{"action": "SLA", "result": "99.95%"}]},
                {"company": "MartCore", "company_stage": "중견", "domain": ["이커머스"], "title": "백엔드 엔지니어", "duration_months": 28,
                 "responsibilities": ["Django+PostgreSQL", "Airflow 도입"],
                 "achievements": [{"action": "마이크로서비스 분리", "result": "8개"}]},
            ],
            "skills": {
                "technical": ["Spark", "Hadoop", "Kafka", "Flink", "Airflow", "dbt", "AWS (EMR/Glue)", "Terraform", "Python", "SQL", "Scala"],
                "domain": ["분산 처리", "스트리밍", "데이터 모델링", "비용 최적화"],
                "language": [{"name": "영어", "level": "Business"}],
            },
            "leadership_signals": ["주니어 3명 멘토링", "코드 리뷰 주 20+ 건", "Apache Airflow 컨트리뷰터"],
            "stability_signals": {"shortest_tenure_months": 28, "longest_tenure_months": 33, "recent_3_avg_months": 30},
        },
    },
    "c06": {
        "id": "c06", "label": "최민준", "primary_jd": "data_engineer",
        "match_keywords": ["최민준", "min-joon", "shopbox"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c06_data_mid.txt"),
        "structured": {
            "candidate_name": "최민준",
            "total_experience_years": 5,
            "current_title": "데이터 분석가 @ ShopBox",
            "career_history": [
                {"company": "ShopBox", "company_stage": "스타트업", "domain": ["이커머스"], "title": "데이터 분석가", "duration_months": 24,
                 "responsibilities": ["Looker 대시보드", "dbt 12개 모델", "BigQuery ETL 일 1천만 건"],
                 "achievements": []},
                {"company": "LearnHub", "company_stage": "스타트업", "domain": ["에듀테크"], "title": "비즈니스 분석가", "duration_months": 25,
                 "responsibilities": ["Tableau 대시보드", "코호트/어트리뷰션 분석"], "achievements": []},
                {"company": "StartFresh", "company_stage": "스타트업", "domain": ["이커머스"], "title": "마케팅 어소시에이트", "duration_months": 6,
                 "responsibilities": ["GA 셋업"], "achievements": []},
            ],
            "skills": {
                "technical": ["SQL", "Python (분석)", "Looker", "Tableau", "dbt", "BigQuery", "Cloud Composer"],
                "domain": ["BI 대시보드", "코호트 분석", "어트리뷰션"],
                "language": [{"name": "영어", "level": "미기재"}],
            },
            "leadership_signals": [],
            "stability_signals": {"shortest_tenure_months": 6, "longest_tenure_months": 25, "recent_3_avg_months": 18},
        },
    },
    "c07": {
        "id": "c07", "label": "조하늘", "primary_jd": "data_engineer",
        "match_keywords": ["조하늘", "ha-neul", "globalcart"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c07_data_strong2.txt"),
        "structured": {
            "candidate_name": "조하늘",
            "total_experience_years": 10,
            "current_title": "데이터 인프라 리드 @ GlobalCart",
            "career_history": [
                {"company": "GlobalCart", "company_stage": "대기업", "domain": ["이커머스"], "title": "데이터 인프라 리드", "duration_months": 46,
                 "responsibilities": ["팀 5명 매니징", "일 120억 건 ETL", "Kafka 50노드"],
                 "achievements": [
                     {"action": "Feast Feature Store", "result": "추천 모델 latency 800→200ms"},
                     {"action": "AWS 비용 절감", "result": "$200K → $130K"},
                 ]},
                {"company": "CommerceLab", "company_stage": "중견", "domain": ["이커머스"], "title": "시니어 데이터 엔지니어", "duration_months": 32,
                 "responsibilities": ["Hadoop → Spark 마이그레이션"], "achievements": [{"action": "성능 향상", "result": "4x"}]},
                {"company": "ServePoint", "company_stage": "중견", "domain": ["서비스"], "title": "백엔드 엔지니어", "duration_months": 41,
                 "responsibilities": ["Django+PostgreSQL", "마이크로서비스"], "achievements": []},
            ],
            "skills": {
                "technical": ["Spark", "Flink", "Kafka", "Airflow", "Argo", "AWS", "K8s", "Terraform", "Python", "Scala", "Go"],
                "domain": ["분산 인프라", "팀 빌딩", "비용 최적화"],
                "language": [{"name": "영어", "level": "Native"}],
            },
            "leadership_signals": ["팀 5명 매니징", "KubeCon 발표", "Apache Spark 기여"],
            "stability_signals": {"shortest_tenure_months": 32, "longest_tenure_months": 46, "recent_3_avg_months": 40},
        },
    },
    "c08": {
        "id": "c08", "label": "한지호", "primary_jd": "data_engineer",
        "match_keywords": ["한지호", "ji-ho", "bannerads"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c08_data_weak.txt"),
        "structured": {
            "candidate_name": "한지호",
            "total_experience_years": 3,
            "current_title": "백엔드 엔지니어 @ BannerAds",
            "career_history": [
                {"company": "BannerAds", "company_stage": "스타트업", "domain": ["광고"], "title": "백엔드 엔지니어", "duration_months": 18,
                 "responsibilities": ["광고 서빙 API", "Cron 배치"], "achievements": []},
                {"company": "MovieFlow", "company_stage": "중견", "domain": ["엔터테인먼트"], "title": "백엔드 어소시에이트", "duration_months": 16,
                 "responsibilities": ["Spring Boot+MySQL", "작은 ETL"], "achievements": []},
            ],
            "skills": {
                "technical": ["Python (Django)", "Java (Spring Boot)", "MySQL", "Redis"],
                "domain": ["백엔드"],
                "language": [{"name": "영어", "level": "Conversational"}],
            },
            "leadership_signals": [],
            "stability_signals": {"shortest_tenure_months": 16, "longest_tenure_months": 18, "recent_3_avg_months": 17},
        },
    },
    "c09": {
        "id": "c09", "label": "서민재", "primary_jd": "growth_marketer",
        "match_keywords": ["서민재", "min-jae", "saascore"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c09_growth_strong.txt"),
        "structured": {
            "candidate_name": "서민재",
            "total_experience_years": 7,
            "current_title": "그로스 마케팅 매니저 @ SaaSCore",
            "career_history": [
                {"company": "SaaSCore", "company_stage": "스타트업", "domain": ["B2B SaaS"], "title": "그로스 마케팅 매니저", "duration_months": 27,
                 "responsibilities": ["월 광고비 1.2억 운영", "Braze 캠페인 18개", "A/B 분기 12+건", "Looker 대시보드 12개"],
                 "achievements": [
                     {"action": "ROAS 개선", "result": "2.4 → 3.8"},
                     {"action": "가입→유료 전환", "result": "+35%"},
                     {"action": "CAC 절감", "result": "₩280K → ₩190K"},
                 ]},
                {"company": "CollabApp", "company_stage": "스타트업", "domain": ["B2B SaaS"], "title": "퍼포먼스 마케터", "duration_months": 33,
                 "responsibilities": ["월 광고비 5천만→1.5억"],
                 "achievements": [{"action": "LinkedIn Ads 신규 도입", "result": "리드 +180%"}]},
                {"company": "AdLab", "company_stage": "중견", "domain": ["광고"], "title": "마케팅 어소시에이트", "duration_months": 19,
                 "responsibilities": ["GA 셋업"], "achievements": []},
            ],
            "skills": {
                "technical": ["Google Ads", "Meta Ads", "LinkedIn Ads", "Braze", "Customer.io", "HubSpot", "SQL", "Mixpanel", "Looker", "VWO", "Python (스크립트)"],
                "domain": ["퍼포먼스 마케팅", "라이프사이클", "A/B 실험", "B2B SaaS"],
                "language": [{"name": "영어", "level": "Business"}],
            },
            "leadership_signals": ["그로스 컨퍼런스 패널"],
            "stability_signals": {"shortest_tenure_months": 19, "longest_tenure_months": 33, "recent_3_avg_months": 26},
        },
    },
    "c10": {
        "id": "c10", "label": "신예린", "primary_jd": "growth_marketer",
        "match_keywords": ["신예린", "ye-rin", "shopflow"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c10_growth_mid.txt"),
        "structured": {
            "candidate_name": "신예린",
            "total_experience_years": 5,
            "current_title": "퍼포먼스 마케팅 매니저 @ ShopFlow",
            "career_history": [
                {"company": "ShopFlow", "company_stage": "스타트업", "domain": ["D2C 이커머스"], "title": "퍼포먼스 마케팅 매니저", "duration_months": 23,
                 "responsibilities": ["월 광고비 9천만 운영", "A/B 분기 5~8건", "BI 쿼리 직접"],
                 "achievements": [{"action": "ROAS", "result": "4.2 (D2C 평균 3.5)"}]},
                {"company": "TrendStore", "company_stage": "스타트업", "domain": ["D2C"], "title": "디지털 마케터", "duration_months": 27,
                 "responsibilities": ["월 광고비 4천만"],
                 "achievements": [{"action": "ROAS 개선", "result": "3.1 → 4.5"}]},
                {"company": "MartConnect", "company_stage": "중견", "domain": ["이커머스"], "title": "마케팅 어소시에이트", "duration_months": 14,
                 "responsibilities": ["SNS 운영"], "achievements": []},
            ],
            "skills": {
                "technical": ["Google Ads", "Meta Ads", "Naver Ads", "SQL (중급)", "Mixpanel", "VWO"],
                "domain": ["퍼포먼스 마케팅 (B2C)", "A/B 테스트"],
                "language": [{"name": "영어", "level": "Conversational"}],
            },
            "leadership_signals": [],
            "stability_signals": {"shortest_tenure_months": 14, "longest_tenure_months": 27, "recent_3_avg_months": 21},
        },
    },
    "c11": {
        "id": "c11", "label": "강태현", "primary_jd": "growth_marketer",
        "match_keywords": ["강태현", "tae-hyun", "brandstudio"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c11_growth_weak.txt"),
        "structured": {
            "candidate_name": "강태현",
            "total_experience_years": 4,
            "current_title": "디지털 마케팅 매니저 @ BrandStudio",
            "career_history": [
                {"company": "BrandStudio", "company_stage": "중견", "domain": ["광고 대행사"], "title": "디지털 마케팅 매니저", "duration_months": 33,
                 "responsibilities": ["광고주 8개 사 운영", "Google/Meta 광고"], "achievements": []},
                {"company": "AdCenter", "company_stage": "중견", "domain": ["광고 대행사"], "title": "AE", "duration_months": 17,
                 "responsibilities": ["광고주 미팅·기획·집행"], "achievements": []},
            ],
            "skills": {
                "technical": ["Google Ads", "Meta Ads", "Excel", "PowerPoint"],
                "domain": ["광고 대행"],
                "language": [{"name": "영어", "level": "미기재"}],
            },
            "leadership_signals": [],
            "stability_signals": {"shortest_tenure_months": 17, "longest_tenure_months": 33, "recent_3_avg_months": 25},
        },
    },
    "c12": {
        "id": "c12", "label": "임소영", "primary_jd": "growth_marketer",
        "match_keywords": ["임소영", "so-young", "paywise"],
        "resume_text": _read_txt(CANDIDATES_DIR / "c12_growth_strong2.txt"),
        "structured": {
            "candidate_name": "임소영",
            "total_experience_years": 9,
            "current_title": "그로스 디렉터 @ PayWise",
            "career_history": [
                {"company": "PayWise", "company_stage": "스타트업", "domain": ["B2B SaaS", "핀테크"], "title": "그로스 디렉터", "duration_months": 33,
                 "responsibilities": ["그로스 팀 6명 빌딩", "월 광고비 1.8억", "PLG 전환 12→21%"],
                 "achievements": [
                     {"action": "ROAS", "result": "2.8 → 4.1"},
                     {"action": "A/B 분기 18+건, 의미 발굴 5건/분기", "result": ""},
                 ]},
                {"company": "CollabHub", "company_stage": "스타트업", "domain": ["B2B SaaS"], "title": "그로스 마케팅 매니저", "duration_months": 39,
                 "responsibilities": ["B2B SaaS 그로스"],
                 "achievements": [{"action": "신규 가입", "result": "월 500 → 5,000건"}]},
                {"company": "MarTechCorp", "company_stage": "중견", "domain": ["광고"], "title": "디지털 마케터", "duration_months": 34,
                 "responsibilities": ["퍼포먼스 + SEO"], "achievements": []},
            ],
            "skills": {
                "technical": ["Google Ads", "Meta Ads", "LinkedIn Ads", "Braze", "Customer.io", "HubSpot", "Marketo", "SQL", "Python (pandas)", "Mixpanel", "Amplitude", "VWO"],
                "domain": ["B2B SaaS 그로스", "PLG", "팀 빌딩", "어트리뷰션 모델링"],
                "language": [{"name": "영어", "level": "Native"}],
            },
            "leadership_signals": ["그로스 팀 6명 빌딩", "B2B SaaS 그로스 컨퍼런스 키노트", "뉴스레터 8K 구독자"],
            "stability_signals": {"shortest_tenure_months": 33, "longest_tenure_months": 39, "recent_3_avg_months": 35},
        },
    },
}


def list_demo_candidates() -> list[dict[str, str]]:
    """앱에서 데모 후보자 풀을 보여줄 때 사용."""
    return [
        {"id": c["id"], "label": c["label"], "current": c["structured"]["current_title"], "primary_jd": c["primary_jd"]}
        for c in CANDIDATE_FIXTURES.values()
    ]


# ============================================================
#  평가 결과 — (jd_id, candidate_id) → result
# ============================================================
#  각 후보자의 primary_jd에 대해서만 풍부하게 작성.
#  다른 JD에 매칭됐을 때는 mock_backend에서 휴리스틱 fallback.
EVALUATION_FIXTURES: dict[tuple[str, str], dict[str, Any]] = {}


# 평가 데이터는 양이 많아 별도 모듈로 분리
from .evaluations import EVALUATIONS  # noqa: E402

EVALUATION_FIXTURES.update(EVALUATIONS)
