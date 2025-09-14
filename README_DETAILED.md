# Shadoway 2025 - Shadow-Aware Pathfinding System
대구 빅데이터 분석대회 본선 진출작

## 개요 (Overview)

Shadoway는 건물 통합정보와 실시간 태양 위치 데이터를 분석하여 시간대별 그림자 영역을 계산하고, 이를 다익스트라 알고리즘에 반영해 "그늘 우선 경로"를 추천하는 시스템입니다.

## 핵심 기능 (Key Features)

1. **실시간 태양 위치 계산 (Real-time Solar Position Calculation)**
   - 정밀한 천문학적 알고리즘을 사용한 태양 위치 계산
   - 위도, 경도, 날짜/시간에 따른 태양의 고도각과 방위각 산출

2. **건물 그림자 시뮬레이션 (Building Shadow Simulation)**
   - 3D 건물 데이터와 태양 위치를 기반으로 그림자 영역 계산
   - 시간대별 그림자 변화 시뮬레이션

3. **그늘 우선 경로 탐색 (Shade-Priority Pathfinding)**
   - 다익스트라 알고리즘에 그림자 정보를 가중치로 반영
   - 최단거리 경로 대비 그늘 제공 경로의 장점 분석

4. **시간대별 경로 최적화 (Time-based Route Optimization)**
   - 하루 중 다양한 시간대에 대한 경로 분석
   - 최적의 출발 시간 추천

## 시스템 구조 (System Architecture)

```
shadoway_main.py          # 메인 시스템 통합 및 데모
├── solar_calculator.py   # 태양 위치 계산 모듈
├── shadow_calculator.py  # 건물 그림자 계산 모듈
├── pathfinder.py        # 그늘 우선 경로 탐색 모듈
└── sample_data.json     # 샘플 건물 및 경로 데이터
```

## 주요 모듈 설명 (Module Description)

### 1. SolarCalculator (태양 위치 계산기)
- **기능**: 주어진 위치와 시간에서의 정확한 태양 위치 계산
- **입력**: 위도, 경도, 날짜/시간
- **출력**: 태양 고도각, 방위각, 천정각

### 2. ShadowCalculator (그림자 계산기)
- **기능**: 건물의 3D 모델과 태양 위치를 기반으로 그림자 영역 계산
- **알고리즘**: 기하학적 투영을 통한 그림자 폴리곤 생성
- **최적화**: 점-폴리곤 충돌 검사 알고리즘 적용

### 3. ShadeAwarePathfinder (그늘 인식 경로 탐색기)
- **기능**: 그림자 정보를 고려한 최적 경로 탐색
- **알고리즘**: 수정된 다익스트라 알고리즘
- **가중치**: 기본 거리 + 그늘 선호도 반영

## 사용법 (Usage)

### 기본 실행
```bash
python3 shadoway_main.py
```

### 개별 모듈 테스트
```bash
# 태양 위치 계산 테스트
python3 solar_calculator.py

# 그림자 계산 테스트  
python3 shadow_calculator.py

# 경로 탐색 테스트
python3 pathfinder.py
```

## 데이터 형식 (Data Format)

### 건물 데이터
```json
{
  "id": "building_001",
  "name": "Sample Building",
  "height": 50.0,
  "footprint": [
    {"x": 0, "y": 0},
    {"x": 20, "y": 0},
    {"x": 20, "y": 30},
    {"x": 0, "y": 30}
  ],
  "type": "office"
}
```

### 경로 노드
```json
{
  "id": "node_001",
  "name": "Station",
  "x": 100.0,
  "y": 200.0
}
```

### 경로 엣지
```json
{
  "from": "node_001",
  "to": "node_002", 
  "distance": 150.0
}
```

## 성능 지표 (Performance Metrics)

실제 테스트 결과 (대구 시내 가상 시나리오):

- **여름 오전 8시**: 그늘 경로 46% vs 최단 경로 17.5% (28.5% 개선)
- **여름 오전 6시**: 그늘 경로 68% vs 최단 경로 32.5% (35.5% 개선)
- **추가 거리**: 평균 15-20m (총 거리의 2-3%)

## 기술적 특징 (Technical Features)

1. **정밀도**: 천문학적 알고리즘 기반 ±1° 정밀도의 태양 위치 계산
2. **효율성**: 그림자 캐싱 및 최적화된 충돌 검사로 실시간 처리 가능
3. **확장성**: 모듈식 구조로 다양한 도시 데이터 적용 가능
4. **실용성**: 실제 도시 환경에서 즉시 적용 가능한 실용적 솔루션

## 응용 분야 (Applications)

- **보행자 내비게이션**: 여름철 그늘 경로 안내
- **도시 계획**: 보행 환경 개선을 위한 건물 배치 최적화
- **관광 안내**: 관광객을 위한 쾌적한 도보 경로 제공
- **헬스케어**: 야외 활동 시 자외선 노출 최소화

## 향후 개선 방안 (Future Enhancements)

1. **실시간 날씨 정보 연동**: 구름, 날씨 정보 반영
2. **동적 장애물 처리**: 나무, 임시 구조물 등 동적 그림자 요소
3. **사용자 선호도 학습**: 개인별 그늘 선호도 맞춤 경로 제공
4. **모바일 앱 통합**: 실시간 위치 기반 경로 안내

## 라이선스 (License)

이 프로젝트는 대구 빅데이터 분석대회 출품작으로 개발되었습니다.

## 기여자 (Contributors)

대구 빅데이터 분석대회 Shadoway 팀