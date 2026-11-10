# Chiikawa Pets for macOS

치이카와 친구들이 맥 화면 아래를 돌아다니는 개인용 데스크톱 펫. 비공식 팬 프로젝트이며 비상업·개인 용도로만 사용한다.

## 에셋 출처와 조건

캐릭터 스프라이트는 [heelee912/chiikawa-dots-pets](https://github.com/heelee912/chiikawa-dots-pets)의
`pets/<id>/spritesheet.png`(투명 PNG, 1536x2288, 192x208 셀)를 그대로 사용한다. 원 저작권은 나가노(ナガノ) 및 권리자에게 있고,
해당 저장소는 **상업적 이용과 재배포를 금지**한다. 그래서 이 저장소에는 이미지가 들어 있지 않으며(`.gitignore`), 앱이 첫 실행 때
사용자의 맥에만 내려받는다. 이 저장소를 공개 배포하거나 에셋이 포함된 `.app`을 나눠 주지 말 것.

GIF(`assets/motions/*.gif`) 대신 스프라이트시트를 쓰는 이유: GIF는 알파 채널이 없고 크림색 배경(#f5f0e8)이 깔려 있어서 펫 주변에
네모 박스가 보인다. 스프라이트시트는 완전 투명이고 상태도 10종이다.

## 실행

```bash
cd /Users/js/orca/chiikawapets
./start.command          # 첫 실행: .venv 생성 + PySide6 설치, 에셋 다운로드 여부를 묻는 창이 뜸
```

수동:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_assets.py   # ~/Library/Application Support/ChiikawaPets/pets 에 저장
python main.py
```

에셋 위치 우선순위: `CHIIKAWA_ASSETS` 환경변수 > `assets/pets/` (저장소 안) > `~/Library/Application Support/ChiikawaPets/pets/`.

## `.app`으로 만들기

```bash
./build_app.sh           # dist/ChiikawaPets.app 생성 (서명 없음)
```

Dock 아이콘 없이 메뉴 바 전용(LSUIElement)으로 동작한다. 에셋은 번들에 넣지 않고 첫 실행 때 내려받는다.
Gatekeeper가 막으면 우클릭 > 열기.

## 조작

| 동작 | 결과 |
|---|---|
| 클릭 | 인사 |
| 더블클릭 | 점프 |
| 드래그 후 놓기 | 던지기: 중력으로 떨어지고 살짝 튕긴 뒤 착지 |
| 마우스 가까이 가져가기 | 가만히 있을 때 시선(16방향)이 커서를 따라옴 |
| 우클릭 | 메뉴: 인사/점프/쉬기/걷기, 잠깐 멈추기, 캐릭터 추가(15종), 파자마 파티즈 소환/단체 춤, 크기, 모든 Space 표시, 숨기기, 종료 |
| 메뉴 바 아이콘 | 우클릭 메뉴와 같은 전역 메뉴 (메뉴 바가 꽉 차 있으면 노치 뒤로 숨을 수 있음) |

자동 행동: 산책, 대기, 인사, 점프, 리뷰, 당황 중에서 무작위로 고르며, 두 마리가 가까이 있으면 가끔 서로 인사한다.
화면 가장자리에서 방향을 바꾸고, Dock 위에 서 있는다. 설정(캐릭터 목록, 크기, Space 옵션)은
`~/Library/Application Support/ChiikawaPets/config.json`에 저장된다.

## 구조

```
chiikawapets/
  catalog.py   캐릭터 목록, 스프라이트시트 레이아웃(상태별 행/프레임/속도)
  pajama.py    파자마 파티즈 4명 스프라이트시트 생성기 (QPainter 벡터 드로잉)
  dance.py     단체 춤 안무: 대형 계산, 모이기, 동기화 춤, 해산
  sprites.py   PNG -> 상태별 QPixmap 프레임 (Retina DPR 반영), 픽셀 히트 테스트, 시선 인덱스
  motion.py    Qt 없는 순수 로직: Animator(프레임), Brain(행동 선택), Body(걷기/점프/중력)
  pet.py       펫 창 하나: 투명 프레임리스 Tool 윈도우, 60Hz 틱, 마우스 입력
  manager.py   펫 생성/제거, 인사 상호작용, 우클릭 메뉴, 메뉴 바 아이콘, 설정 반영
  macos.py     ctypes로 Cocoa 호출: Dock 아이콘 숨김, 모든 Space 표시, 전체화면 위 표시
  config.py    설정 저장/검증   paths.py 경로   download.py 에셋 다운로드   app.py 진입점
tests/         motion, config 단위 테스트 (pytest)
```

파일당 300줄, 함수당 50줄 이하를 유지한다.

## 테스트

```bash
.venv/bin/python -m pytest -q
```

## 파자마 파티즈

원본 저장소에 파자마 파티즈가 없어서 `chiikawapets/pajama.py`가 네 멤버(초록·분홍·보라·흰색)를 QPainter로 직접 그려
같은 레이아웃의 스프라이트시트를 만든다. 얼굴 없는 후드, 사선 홍조 자국, 단추 2개, 멤버별 귀/뿔/꼬리를 포즈 파라미터로
표현하며 기본 10개 상태에 더해 단체 춤 전용 상태 4개(볼에 손 대기, 두 손 들기, 제자리 회전, 뒤돌아 엉덩이 흔들기)를
11~14행에 추가한 15행짜리 시트를 생성한다. 생김새와 안무는 애니메이션 댄스 장면 GIF를 보고 맞췄다. 첫 실행 때 없으면 자동 생성되고, 수동 재생성은
`python scripts/make_pajama_sheets.py`. 우클릭 메뉴의 "파자마 파티즈 4명 소환"으로 한 번에 부를 수 있다.
이 그림은 이 저장소의 팬아트이며 마찬가지로 비상업·개인 용도다.

### 단체 춤

`chiikawapets/dance.py`의 `GroupDance`가 파자마 파티즈를 아이돌처럼 모아서 춤추게 한다. 멤버가 2명 이상이면
3~7분마다 자동으로, 또는 우클릭 메뉴 "파자마 파티즈 단체 춤"으로 시작한다. 흐름: 멤버들이 현재 위치의 평균점으로
걸어가 일렬 대형(`formation_slots`)에 선다 → 전원 도착(또는 25초 경과) 시 `ROUTINE`(볼 포즈 → 손 들기 → 회전 →
엉덩이 흔들기 반복, 약 15초)을 전원 같은 순간에 전환하며 춘다. 볼 포즈만 옆 사람과 반대 손이고 나머지는 일제히 같다 →
다른 펫들은 손을 흔들며 응원 → 끝나면 인사하고 자유 행동으로 돌아간다.
춤추는 동안 해당 펫은 `locked` 상태라 무작위 행동과 인사 상호작용이 멈추고, 사용자가 메뉴로 다른 동작을 시키면 바로 풀린다.

## 알려진 제한

- 파자마 파티즈 그림은 코드로 그린 근사치라 원작의 선 맛과는 차이가 있다. 모양을 바꾸려면 `pajama.py`의 `MEMBERS`와
  `PajamaPainter`를 수정하고 재생성하면 된다.
- 다른 창 위에 "앉기", 창 가장자리에 매달리기는 아직 없다.
- 단체 춤의 동기화는 펫마다 따로 도는 16ms 타이머에 의존하므로 프레임 전환이 최대 한 틱(16ms) 어긋날 수 있다.
- 멀티 모니터: 펫이 있는 화면 기준으로 바닥/가장자리를 계산하지만, 처음 등장 위치는 주 모니터다.
