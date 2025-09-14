# Shadoway 2025 - Shadow-Aware Pathfinding System
대구 빅데이터 분석대회 본선 진출작 Shadoway 레포지토리입니다.

## 시스템 개요

건물 통합정보와 실시간 태양 위치 데이터를 분석해 시간대별 그림자 영역을 계산하고, 이를 다익스트라 알고리즘에 반영해 **'그늘 우선 경로'**를 추천하는 혁신적인 내비게이션 시스템입니다.

## 🌟 주요 기능

- ☀️ **실시간 태양 위치 계산**: 정밀한 천문학적 알고리즘
- 🏢 **3D 건물 그림자 시뮬레이션**: 시간대별 그림자 영역 예측
- 🛣️ **그늘 우선 경로 탐색**: 다익스트라 알고리즘 기반 최적화
- ⏰ **시간대별 경로 분석**: 최적 출발 시간 추천
- 📊 **성능 비교**: 최단거리 vs 그늘우선 경로 분석

## 🚀 실행 방법

```bash
# 메인 시스템 실행
python3 shadoway_main.py

# 개별 모듈 테스트
python3 solar_calculator.py
python3 shadow_calculator.py  
python3 pathfinder.py

# 시각화 생성 (matplotlib 필요)
python3 visualizer.py
```

## 📈 성능 결과

대구 시내 가상 시나리오 기준:
- **여름 오전 6시**: 그늘 경로 68% vs 최단 경로 32.5% (+35.5% 개선)
- **여름 오전 8시**: 그늘 경로 46% vs 최단 경로 17.5% (+28.5% 개선)
- **추가 거리**: 평균 15-20m (2-3% 증가로 상당한 그늘 혜택 제공)

## 📁 파일 구조

```
├── shadoway_main.py      # 메인 통합 시스템
├── solar_calculator.py   # 태양 위치 계산
├── shadow_calculator.py  # 건물 그림자 계산  
├── pathfinder.py        # 그늘 우선 경로 탐색
├── sample_data.json     # 샘플 데이터
├── visualizer.py        # 시각화 도구
└── README_DETAILED.md   # 상세 문서
```

## 🎯 활용 분야

- 보행자 내비게이션 (여름철 쾌적한 경로 안내)
- 도시 계획 (보행 친화적 환경 설계)
- 관광 안내 (관광객 편의 증진)
- 헬스케어 (자외선 노출 최소화)

자세한 내용은 [README_DETAILED.md](README_DETAILED.md)를 참조하세요.
