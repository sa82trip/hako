# Changelog

## [content → git submodule 전환] - 2026-07-03

**Branch**: `main` | **Commit**: 4a8af12 "add content as submodule" (fast-forward push to origin/main)

### Added
- `.gitmodules` — `content` 서브모듈 등록 (`https://github.com/sa82trip/hako-contents.git`, branch `main`)
- `content` — submodule gitlink (pinned `e9712cd` = heads/main)

### Removed
- `content/*.md`, `content/templates/*`, `content/.gitkeep` — 인레포 콘텐츠 파일 일괄 삭제 (서브모듈이 정본)
- `content/LLM/루프-엔지니어링.md`, `content/LLM/하네스-엔지니어링.md` — 과거 인레포 구조(LLM/ 하위). 서브모듈은 content/ 루트에 동일 문서 보관
- `content/Drafts/Untitled.md` — 빈 초안

### Technical Notes
- **SSH→HTTPS**: 최초 요청된 SSH URL(`git@github.com:sa82trip/hako-contents.git`) 은 `Permission denied (publickey)` 로 실패. `~/.ssh/config` 에 GitHub 설정 없고 에이전트 키 미로드. HTTPS URL 로 대체.
- **Push 충돌 해결**: 로컬 커밋 push 시 원격 `vault backup` 커밋 3개(2026-07-03 08:22~09:11) 가 content/ 를 일반 파일로 되돌려 non-fast-forward 발생. 해당 content 변경은 서브모듈(2026-07-03 10:44 init, 더 최신) 에 이미 흡수됨을 확인(`content/index.md` 등 본문 동일; 차이는 LLM/ 경로·Obsidian 표 패딩·빈 Drafts 초안 정도).
- **비파괴 해결**: `git reset --soft origin/main` 로 커밋 부모를 origin/main 으로 이동 후 재커밋. 인덱스가 이미 "content=gitlink" 트리라 origin/main 대비 "content/ 파일 제거 + gitlink + .gitmodules" 단일 커밋이 됨. force push 없이 `ad9de59..4a8af12` fast-forward push 로 백업 히스토리 보존.
- Total: 14 files changed, 5 insertions(+), 566 deletions(-)

---

## [보류: deploy.yml 서브모듈 CI 통합] - 2026-07-03

**상태**: 미커밋(작업자 외 변경, 사용자 결정 대기)

### Changed (작업자 외, 미커밋)
- `.github/workflows/deploy.yml` — `actions/checkout` 뒤 PAT 인증(CONTENT_PAT) + `git submodule update --remote --recursive` 단계 추가. 서브모듈을 배포 빌드에 포함시키기 위함.

### 비고
- checkout 단계에 `submodules: true` 가 없어, 이 변경이 없으면 배포 시 content 가 비게 됨.
- hako-contents 는 public 이라 PAT 는 private 전환 대비용.
