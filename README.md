# 24: The Game (PS2) 비공식 한글패치

PS2 북미판 **24: The Game (SLUS-21268)** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·영어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `.iso`** (Redump 형식)를 준비합니다. CSO·CHD 등으로 변환한 이미지에는 적용할 수 없습니다.
2. xdeltaUI 같은 도구로 원본 ISO에 `24TheGame_KO_v1.0.xdelta`를 적용합니다.
   - 명령줄: `xdelta3 -d -s "24 - The Game (USA) (En,Fr,Es).iso" 24TheGame_KO_v1.0.xdelta "24 - The Game (USA) (Korean).iso"`
3. 만들어진 ISO를 PCSX2 등에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 ISO 크기 | 4,562,092,032 바이트 |
| 원본 ISO MD5 | `f60b2cdb21a40d06c2febdf2381b7891` |
| 원본 ISO SHA-256 | `49ddf50e6f8633ec6cdd31576bbd308c384f0880c87138ad20f96bd728f8b4c0` |
| xdelta SHA-256 | `f48de74f4b4829651c0b555fd512bd34b98f10d400c1ed010325220314b965f5` |
| 결과 ISO 크기 | 4,564,217,856 바이트 |
| 결과 ISO SHA-256 | `cccf9baec54cd0f4c343bcc3011d922fb63ba083b1fa1f9b4f05108d89f20744` |
| 게임 CRC (PCSX2) | `F1C7201E` (실행 파일은 원본 그대로) |

## 주의
- 원본에서 만든 상태저장은 불러오지 마세요. 메모리 카드 세이브는 그대로 쓸 수 있습니다.
- 자막은 기본값이 **꺼짐**입니다. 설정 → 언어 → 자막을 **켬**으로 바꾸세요. 언어(영어·프랑스어·스페인어)는 무엇을 골라도 한국어로 나옵니다.
- 16:9 화면은 게임 자체 옵션(설정 → 비디오 → 와이드스크린)을 켜고, PCSX2 화면비를 16:9로 맞추면 됩니다. 별도 와이드 패치는 필요 없습니다.
- xdelta는 압축하지 않은 형식(`-0`)입니다.

## 한글화 내용
- 메뉴·도움말·임무 목표·PDA·튜토리얼·컷신/무전 자막 등 게임 문자열 4,624종 전체 직접 번역
- 영어·프랑스어·스페인어 언어 설정 모두 한국어 파일을 가리키도록 수정
- 게임 글꼴 5종에 한글 추가(본문 925자, 메뉴 592자, 짧은 제목 288자), 쓰이지 않는 악센트 글자 제거로 메모리 확보
- 임무 평가 탭 등 칸 넘침 정리

## 문서
- [CHANGELOG.md](CHANGELOG.md), [docs/BUILD.md](docs/BUILD.md), [docs/TECH.md](docs/TECH.md), [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md), [RIGHTS.md](RIGHTS.md)
