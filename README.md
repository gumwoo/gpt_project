# 데이터 스토리텔러

데이터 스토리텔러는 복잡한 데이터를 분석하여 의미 있는 인사이트를 추출하고, 이를 이해하기 쉬운 내러티브 형식으로 변환하여 효과적인 데이터 기반 스토리텔링을 지원하는 애플리케이션입니다.

## 주요 기능

- CSV 파일 업로드 및 기본 분석
- GPT API를 활용한 데이터 스토리 자동 생성
- 데이터 인사이트 추출 및 시각화
- 다양한 청중(경영진, 마케팅팀, 기술팀, 일반 대중)에 맞춘 내러티브 생성
- 데이터 기반 액션 아이템 제안

## 설치 방법

1. 저장소 클론:
```
git clone <repository-url>
cd data-storyteller
```

2. 필요한 패키지 설치:
```
pip install -r requirements.txt
```

3. API 키 설정:
```
# .env 파일 생성
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

4. 실행:
```
streamlit run app.py
```

## API 키 설정

이 애플리케이션은 OpenAI API를 사용하므로 API 키가 필요합니다:

1. OpenAI 계정에서 API 키를 발급받습니다 (https://platform.openai.com/api-keys)
2. 프로젝트 루트 디렉토리에 `.env` 파일을 생성합니다
3. 파일에 다음 내용을 추가합니다:
```
OPENAI_API_KEY=your_api_key_here
```
4. `.env` 파일은 `.gitignore`에 포함되어 있으므로 Git에 추가되지 않습니다

## 사용 방법

1. 웹 브라우저에서 `http://localhost:8501` 접속
2. CSV 파일을 업로드하거나 샘플 데이터 사용
3. 사이드바에서 대상 청중, 스토리 중점, 길이 등 설정 조정
4. "데이터 스토리 생성" 버튼 클릭
5. 생성된 데이터 스토리와 시각화 확인

## 샘플 데이터

애플리케이션에는 다음과 같은 샘플 데이터가 포함되어 있습니다:

- **판매 데이터**: 날짜, 지역, 제품 카테고리, 판매액, 판매량 등
- **마케팅 캠페인 데이터**: 캠페인 ID, 채널, 비용, 노출, 클릭, 전환 등
- **고객 만족도 조사**: 고객 정보, 평가 점수, 피드백 등

## 프로젝트 구조

```
data_storyteller/
├── app.py                  # 메인 애플리케이션 파일
├── prompts.py              # GPT 프롬프트 템플릿
├── data_loader.py          # 데이터 로딩 및 처리 모듈
├── data_visualizer.py      # 데이터 시각화 모듈
├── utils.py                # 유틸리티 함수
├── requirements.txt        # 필요한 패키지 목록
├── .env                    # 환경 변수 파일 (API 키 등)
├── .gitignore              # Git 무시 파일 목록
├── README.md               # 프로젝트 설명
└── sample_data/            # 샘플 데이터 폴더
    ├── sales_data.csv
    ├── marketing_campaign.csv
    └── customer_satisfaction.csv
```

## GPT API 활용

이 애플리케이션은 OpenAI의 GPT API를 활용하여 데이터 분석 결과를 자연어 스토리로 변환합니다. API 호출은 다음과 같은 요소를 포함합니다:

- 데이터 분석 결과의 JSON 형식 전달
- 타겟 청중에 따른 커뮤니케이션 스타일 조정
- 스토리 중점 영역 (트렌드, 이상치, 상관관계 등) 지정
- 구조화된 JSON 형식의 응답 요청

## 한글 데이터 지원

- 다양한 인코딩의 CSV 파일을 자동으로 감지하여 처리합니다 (UTF-8, CP949, EUC-KR 등)
- 한글 폰트를 자동으로 감지하여 시각화에 적용합니다
- 운영체제별로 적합한 한글 폰트를 선택합니다

## 향후 개선 계획

- 더 다양한 데이터 형식 지원 (Excel, JSON, SQL 등)
- 고급 분석 기능 추가 (예측 분석, 세그먼트 분석 등)
- 프레젠테이션 템플릿 기능 확장
- 실시간 데이터 소스 연결 지원
- 사용자 피드백 기반 스토리 품질 향상
