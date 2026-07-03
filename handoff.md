# hako - 개인 위키 (Quartz + GitHub Pages)

## 현재 상태
**Phase**: content 콘텐츠 분리 완료 — `content/` 가 독립 저장소 `hako-contents` 의 git submodule 이 됨
**다음 작업**: 미커밋 변경 `.github/workflows/deploy.yml`(서브모듈 CI 통합) 커밋 여부 결정 → 배포 동작 검증

## 최근 작업

### 2026-07-03: content 를 git submodule 로 전환
- **브랜치**: `main`
- **커밋**: `4a8af12` "add content as submodule" (origin/main 에 fast-forward push 됨)

**Submodule:**
- `content` → `https://github.com/sa82trip/hako-contents.git`, branch `main`, pinned `e9712cd`(heads/main)
- `.gitmodules` 추가
- 기존 인레포 content/ 파일 일괄 삭제(LLM/, Drafts/ 포함). 콘텐츠 본문은 서브모듈이 정본.

**해결 과정:**
- 최초 SSH URL(`git@github.com:...`) 은 publickey 인증 실패 → HTTPS 로 대체
- push 시 원격의 `vault backup` 커밋 3개(08:22~09:11)와 충돌. 이들 content/ 변경은 서브모듈(10:44 생성, 더 최신)에 이미 흡수됨.
- `git reset --soft origin/main` 후 재커밋 → 백업 히스토리 보존 + force push 없이 fast-forward push 해결

## 알려진 이슈
- **`.github/workflows/deploy.yml` 미커밋 변경 있음**(내 작업 아님). 서브모듈을 CI 배포에 통합하는 설정(PAT 인증 + `git submodule update --remote --recursive`). 현재 checkout 단계에 `submodules: true` 가 없어, 이 변경 없으면 배포 시 content 가 빈 채로 빌드될 수 있음. 커밋 필요 여부 사용자 결정 대기.
- hako-contents 저장소는 public 이라 PAT 없이도 clone 됨. deploy.yml 의 PAT 단계는 private 전환 시 대비용.

## TODO
1. deploy.yml 서브모듈 통합 설정 커밋/검토
2. GitHub Actions 배포가 content 서브모듈을 정상 빌드하는지 확인
3. (선택) 루프·하네스 문서 경로 — 서브모듈은 `content/` 루트, 과거 인레포는 `content/LLM/` 하위. 구조 정리 필요 시 hako-contents 에서.
