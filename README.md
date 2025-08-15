# 한국기사 FDA/EMA 승인 뉴스 자동 업데이트 사이트

이 리포지토리는 **한국어 뉴스**에서 `FDA 승인/허가`, `EMA 승인/허가` 키워드를 **Google News RSS**로 수집해, 매일 1회 자동으로 `data/latest.json`을 갱신하고, 정적 웹페이지(`index.html`)에서 보여줍니다. 별도 서버나 유료 API 없이 **GitHub Pages + GitHub Actions** 조합으로 동작합니다.

## 빠른 시작

1. 본 폴더를 GitHub 새 리포지토리로 업로드
2. Settings → Pages에서 **Branch: `main` / `/ (root)`**로 설정해 배포
3. Actions 탭에서 워크플로우 허용 (첫 실행 수동 `Run workflow` 가능)
4. 브라우저에서 리포지토리 Pages URL 접속 → 뉴스 확인

> 기본 cron은 **매일 00:10 KST (UTC 15:10)** 입니다. `/.github/workflows/daily.yml`에서 변경할 수 있습니다.

## 동작 원리

- `scripts/fetch_news.py`가 Google News RSS(ko-KR)에서 FDA/EMA 관련 한국어 기사를 수집
- 제목/요약을 기반으로 **FDA/EMA 라벨**을 판별(간단 키워드 매칭)
- 결과를 `data/latest.json` 및 `data/YYYY-MM-DD.json`으로 저장
- 정적 페이지(`index.html`)가 `data/latest.json`을 불러와 카드 리스트로 표시
- GitHub Actions가 매일 1회 실행하여 자동 커밋/배포

## 커스터마이징

- 검색 키워드: `scripts/fetch_news.py`의 `QUERIES` 배열 수정
- 라벨 로직: `guess_label()`에서 키워드/규칙 보완
- 한국 매체 한정: `is_korean_source()`와 `KOREAN_TLDS` 보완
- UI: `/assets/style.css`, `/assets/app.js`

## 로컬 테스트

```bash
pip install feedparser
python scripts/fetch_news.py
# 생성된 data/latest.json을 브라우저로 index.html과 함께 열면 됩니다.
```

## 주의사항

- Google News RSS는 언론사 헤드라인의 **키워드 매칭**이므로, 100% 정확한 '실제 승인 완료' 기사만 나오지는 않을 수 있습니다.
  - 필요 시 스크립트에 **강화 필터**(예: "최종 승인", "품목허가 획득", "시판허가", 임상 단계 제외 등)를 추가하세요.
- 기업 국적 판별이 필요하다면, **국내 상장사 목록**을 사전 테이블로 두고 제목/본문에서 매칭하는 방식을 추천합니다.
- 상업적 사용 시 각 뉴스 사이트의 저작권/링크 정책을 준수하세요.
