# fdd-valuation-dashboard
M&amp;A FDD and EV/EBITDA valuation automation prototype using Streamlit
# 📊 M&A FDD & Valuation Dashboard (재무실사 및 가치평가 시뮬레이터)

> **M&A 재무실사(FDD)의 핵심 프로세스인 '이익의 질(Quality of Earnings, QoE) 분석'과 '멀티플 기반 밸류에이션 시뮬레이션'을 데이터 기반으로 시각화한 Python & Streamlit 프로토타입 프로젝트입니다.**
> 본 프로젝트는 실무자가 수많은 계정별 원장을 보며 수작업으로 일회성 손익을 조정하는 비효율을 개선하고, 주요 재무 지표의 하방 리스크(Downside Risk)를 실시간으로 스크리닝하여 신속하고 정교한 투자 의사결정을 지원하도록 설계되었습니다.

---

## ✨ 핵심 구현 기능 (3대 실무 통제 로직)

### 1. QoE (이익의 질) 분석 & Waterfall 시각화
* **목적**: 피인수기업의 회계적 착시 손익을 제거하고, 인수 후에도 지속 가능한 진짜 기초 체력인 '조정 이익(Normalized EBITDA)' 산출
* **로직**: 가상 3개년 손익계산서(IS)를 기반으로 **비경상적 손익(Non-recurring)**, **대주주 관련 사적 비용(Owner's Expense)**, **회계정책 차이 조정(Accounting Adj)** 등 실무 주요 조정 항목을 자동 가감
* **시각화**: Plotly 라이브러리의 **Waterfall(폭포) 차트**를 적용하여, 원래 EBITDA에서 각 조정 항목을 거쳐 Normalized EBITDA로 도달하는 흐름을 시각적으로 구현

### 2. 운전자본(Working Capital) 리스크 동적 스크리닝
* **목적**: 인수 후 매수인이 부담해야 할 추가 자금(Net Working Capital) 규모 예측 및 부실 자산 리스크 탐지
* **로직**: 3개년 매출채권 회전기일(DSO) 및 재고자산 회전기일(DIO) 추적
* **동적 경고 시스템**: 전년 대비 회전기일이 **15% 이상 급증**하는 부실 징후 포착 시, 대시보드 상단에 `🚨 경고: 부실자산 및 가공매출 위험성 정밀 실사 필요` 배너를 동적으로 출력하여 실사 중점 영역(Scope) 가이드

### 3. 인터랙티브 Valuation & 주식가치(Equity Value) 산출
* **목적**: 조정 실적 및 시장 멀티플 변동에 따른 기업 가치의 민감도 실시간 시뮬레이션
* **로직**: `st.slider`를 활용해 유사동종그룹 EV/EBITDA 멀티플(5배 ~ 15배)을 동적 조절
* **재무 수식 정밀화**: 단순히 기업가치(EV)만 구하는 것에 그치지 않고, 실무 관점을 반영해 **순부채(Net Debt)**를 차감함으로써 주주가 실제로 가져가는 **최종 주식가치(Equity Value)**까지 실시간 동적 계산 (`Equity Value = EV - Net Debt`)

---

## 📈 Mock Data 시나리오 및 기능 검증 결과

본 프로그램의 실무 정밀도 검증을 위해 3개년 요약 재무제표 시나리오를 주입하여 시스템 테스트를 완료했습니다.

* **EBITDA 조정 검증**: 비경상 비용(소송 합의금 등) 및 대주주 급여 조정을 통해 EBITDA가 정상적으로 Normalized되는 흐름 검증
* **NWC 경고 시스템 검증**: 3차년도 매출채권 회전기일이 전년 대비 15% 이상 급증하는 시나리오 주입 시, 대시보드 상단에 즉각적인 위험 경고 배너 렌더링 확인
* **밸류에이션 민감도 연동**: 멀티플 슬라이더 및 순부채 입력값 조정에 따라 EV 및 Equity Value 수식이 실시간 새로고침되는 인터랙티브 UI 검증

---

## 🚀 직접 테스트해보기 (How to Test)

> 💡  본 프로그램은 동적 파일 업로드 기능을 지원하므로, 실제 준비된 데이터셋을 통해 실시간 동적 분석 및 시각화 프로세스를 테스트해보실 수 있습니다.
> 
>  
> 1. 실행된 웹 화면 좌측 사이드바의 **[Browse files]** 버튼을 통해 해당 파일을 업로드합니다.
> 2. 만약 업로드된 파일이 없을 경우, 내장된 **3개년 표준 가상 데이터(Mock Data)**가 자동으로 로드되어 대시보드가 정상 작동합니다.

---

## 🛠️ 기술 스택 및 실행 방법

* **Language**: Python 3.x
* **Libraries**: Pandas, Streamlit, Plotly
* **로컬 실행 명령어**:
  ```bash
  pip install -r requirements.txt
  streamlit run app_deals.py
