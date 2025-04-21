"""
데이터 스토리텔러 애플리케이션에서 사용하는 프롬프트 템플릿을 관리하는 모듈입니다.
"""

import json

def generate_data_story_prompt(dataframe_info, audience, focus, length, sample_data):
    """
    데이터 스토리 생성을 위한 프롬프트를 생성합니다.
    
    Args:
        dataframe_info (dict): 데이터프레임 분석 결과
        audience (str): 타겟 청중 (경영진, 마케팅팀, 기술팀, 일반 대중)
        focus (str): 분석 중점 (주요 트렌드, 이상치, 상관관계, 종합 인사이트)
        length (str): 스토리 길이 (간결, 보통, 상세)
        sample_data (dict): 샘플 데이터 (최대 10행)
    
    Returns:
        str: GPT API에 전달할 프롬프트
    """
    
    # 데이터 정보를 JSON 문자열로 변환
    # 너무 큰 JSON은 잘라내기
    # basic_info와 중요 통계만 포함
    simplified_info = {
        "basic_info": dataframe_info.get("basic_info", {}),
        "column_summary": {}
    }
    
    # 주요 열에 대한 통계 요약
    numeric_stats = dataframe_info.get("numeric_stats", {})
    categorical_stats = dataframe_info.get("categorical_stats", {})
    
    # 통계 정보 간소화
    if isinstance(numeric_stats, dict):
        for col, stats in numeric_stats.items():
            if isinstance(stats, dict):
                simplified_info["column_summary"][col] = {
                    "type": "numeric",
                    "mean": stats.get("mean"),
                    "min": stats.get("min"),
                    "max": stats.get("max")
                }
    
    if isinstance(categorical_stats, dict):
        for col, stats in categorical_stats.items():
            if isinstance(stats, dict):
                # 상위 3개 카테고리만 포함
                top_categories = dict(list(stats.items())[:3])
                simplified_info["column_summary"][col] = {
                    "type": "categorical",
                    "top_categories": top_categories
                }
    
    # 상관관계 정보 (중요한 경우에만)
    if "correlation" in dataframe_info:
        # 상관계수 0.5 이상인 경우만 포함
        high_correlations = []
        corr_data = dataframe_info["correlation"]
        if isinstance(corr_data, dict):
            for col1, corr_vals in corr_data.items():
                if isinstance(corr_vals, dict):
                    for col2, val in corr_vals.items():
                        if col1 != col2 and abs(val) >= 0.5:
                            high_correlations.append({
                                "column1": col1,
                                "column2": col2,
                                "correlation": val
                            })
        
        if high_correlations:
            simplified_info["high_correlations"] = high_correlations
    
    # JSON 문자열로 변환
    dataframe_info_str = json.dumps(simplified_info, ensure_ascii=False, indent=2)
    
    # 샘플 데이터 간소화 (최대 5행)
    sample_data_simplified = {}
    if isinstance(sample_data, dict):
        for col, values in sample_data.items():
            if isinstance(values, dict):
                sample_data_simplified[col] = dict(list(values.items())[:5])
    
    sample_data_str = json.dumps(sample_data_simplified, ensure_ascii=False, indent=2)
    
    # 청중별 특성 정의
    audience_characteristics = {
        "경영진": "비즈니스 의사결정자로, 핵심 비즈니스 영향과 전략적 인사이트에 관심이 있습니다. 기술적 세부사항보다는 비즈니스 가치와 실행 가능한 인사이트를 선호합니다.",
        "마케팅팀": "마케팅 전문가로, 고객 행동, 세그먼트, 캠페인 성과, 시장 트렌드에 관심이 있습니다. 비즈니스 가치와 전략적 마케팅 인사이트를 선호합니다.",
        "기술팀": "데이터 및 기술 전문가로, 심층적인 분석과 기술적 세부사항에 관심이 있습니다. 통계적 의미, 방법론, 데이터 품질에 대한 언급을 선호합니다.",
        "일반 대중": "데이터 분석에 대한 전문 지식이 부족할 수 있으며, 복잡한 기술 용어보다는 일상적인 언어로 설명된 인사이트를 선호합니다."
    }
    
    # 분석 중점별 지시사항
    focus_instructions = {
        "주요 트렌드": "데이터에서 시간에 따른 변화, 성장/감소 패턴, 반복되는 사이클 등 주요 트렌드를 식별하고 설명하세요.",
        "이상치 및 특이점": "데이터에서 특이한 패턴, 이상치, 예상과 다른 값, 특별한 관심이 필요한 영역을 식별하고 설명하세요.",
        "상관관계 분석": "데이터에서 변수 간의 관계, 상관성, 인과 가능성을 분석하고 설명하세요.",
        "종합 인사이트": "데이터에서 비즈니스 가치가 있는 종합적인 인사이트를 도출하고, 가능한 액션 아이템을 제시하세요."
    }
    
    # 길이별 지시사항
    length_instructions = {
        "간결": "핵심 포인트만 간결하게 요약하여 설명하세요. 전체 응답은 3-4개의 주요 인사이트와 짧은 설명으로 구성하세요.",
        "보통": "주요 인사이트와 그 의미를 균형 있게 설명하세요. 세부 정보와 예시를 적절히 포함하세요.",
        "상세": "인사이트의 깊이 있는 분석, 다양한 예시, 세부 설명, 추가 컨텍스트를 포함한 상세한 설명을 제공하세요."
    }
    
    # 프롬프트 템플릿
    prompt = f"""
당신은 데이터 분석 전문가이자 스토리텔링 전문가입니다. 주어진 데이터를 분석하고, '{audience}'를 위한 통찰력 있는 데이터 스토리를 생성해주세요.

## 대상 청중 정보:
{audience_characteristics.get(audience, "일반적인 독자")}

## 분석 중점:
{focus_instructions.get(focus, "데이터에서 주요 인사이트를 찾아 설명하세요.")}

## 원하는 스토리 길이:
{length_instructions.get(length, "균형 잡힌 설명을 제공하세요.")}

## 데이터 분석 정보:
```json
{dataframe_info_str}
```

## 샘플 데이터 (일부):
```json
{sample_data_str}
```

## 응답 형식:
당신의 응답은 반드시 다음 구조를 가진 JSON 형식이어야 합니다:

```json
{{
  "key_insights": [
    {{
      "title": "인사이트 제목",
      "description": "인사이트에 대한 상세 설명",
      "chart_recommendation": {{
        "type": "차트 유형(bar, line, scatter 등)",
        "x_column": "x축에 사용할 열 이름",
        "y_column": "y축에 사용할 열 이름",
        "title": "차트 제목",
        "description": "이 차트가 왜 유용한지 설명"
      }}
    }}
  ],
  "narrative": "데이터를 스토리텔링 형식으로 설명하는 전체 내러티브 텍스트",
  "recommended_actions": [
    {{
      "title": "액션 제목",
      "description": "권장 액션에 대한 설명"
    }}
  ]
}}
```

중요: 응답은 반드시 유효한 JSON 형식이어야 합니다. key_insights에는 3-5개의 주요 인사이트를 포함하고, 각 인사이트에는 가능하면 적절한 차트 추천을 포함하세요. narrative는 데이터의 전체적인 스토리를 설명하는 응집력 있는 텍스트입니다. recommended_actions에는 데이터 기반의 2-4개 실행 가능한 추천사항을 포함하세요.

차트 추천 시 샘플 데이터에 있는 실제 열 이름을 사용해야 합니다. 존재하지 않는 열 이름은 사용하지 마세요.
"""
    
    return prompt


def generate_insights_prompt(dataframe_info, specific_question):
    """
    특정 질문에 대한 인사이트 생성을 위한 프롬프트를 생성합니다.
    
    Args:
        dataframe_info (dict): 데이터프레임 분석 결과
        specific_question (str): 사용자의 특정 질문
    
    Returns:
        str: GPT API에 전달할 프롬프트
    """
    
    # 데이터 정보를 JSON 문자열로 변환
    dataframe_info_str = json.dumps(dataframe_info, ensure_ascii=False, indent=2)
    
    # 프롬프트 템플릿
    prompt = f"""
당신은 데이터 분석 전문가입니다. 주어진 데이터를 분석하고, 사용자의 특정 질문에 대한 통찰력 있는 답변을 생성해주세요.

## 사용자 질문:
{specific_question}

## 데이터 분석 정보:
```json
{dataframe_info_str}
```

## 응답 형식:
당신의 응답은 반드시 다음 구조를 가진 JSON 형식이어야 합니다:

```json
{{
  "answer": "질문에 대한 직접적인 답변",
  "explanation": "답변에 대한 상세 설명과 근거",
  "data_points": [
    "답변을 뒷받침하는 주요 데이터 포인트 1",
    "답변을 뒷받침하는 주요 데이터 포인트 2"
  ],
  "limitations": "이 분석의 한계 또는 주의사항",
  "chart_recommendation": {{
    "type": "차트 유형(bar, line, scatter 등)",
    "x_column": "x축에 사용할 열 이름",
    "y_column": "y축에 사용할 열 이름",
    "title": "차트 제목",
    "description": "이 차트가 어떻게 질문에 답하는데 도움이 되는지 설명"
  }}
}}
```

중요: 응답은 반드시 유효한 JSON 형식이어야 합니다. 질문에 직접적으로 답하고, 데이터에서 얻은 증거로 뒷받침하세요. 데이터가 질문에 완전히 답하기에 충분하지 않은 경우, 한계를 명확히 설명하세요.
"""
    
    return prompt
