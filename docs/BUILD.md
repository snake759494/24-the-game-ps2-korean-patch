# 빌드 방법

1. 원본 ISO `24 - The Game (USA) (En,Fr,Es).iso`와 나눔스퀘어 네오 TTF를 작업 폴더 최상위에 둡니다.
2. `python tools/extract.py`로 영어 원문 목록(`translation/source.json`)을 만듭니다.
3. 번역 파일(저장소 미포함)을 `translation/ko/*.tsv`(번호<TAB>번역)로 둡니다. `python tools/check.py`로 누락·제어 코드 검사.
4. `python tools/build.py`로 원본 옆에 `24 - The Game (USA) (Korean).iso`를 만듭니다.
5. `xdelta3 -e -0 -s 원본.iso 한글판.iso 패치.xdelta`로 압축 없는 xdelta를 만듭니다.

필요: Python 3, Pillow, NumPy.
