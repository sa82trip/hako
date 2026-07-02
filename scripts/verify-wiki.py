#!/usr/bin/env python3
"""verify-wiki.py — Quartz 위키 페이지 검증.

사용법:
  python3 verify-wiki.py <파일.md>          # 단일 파일
  python3 verify-wiki.py <content-디렉토리>  # 디렉토리 내 .md 전체 (templates/ 제외)

검사 항목:
  1. frontmatter — title 필수
  2. 코드 펜스(``` ~~~) 밸런스
  3. 빈 섹션 — 헤딩 다음에 내용 없이 다음 헤딩/EOF
  4. 위키링크 [[X]] 대상 존재 (shortest 매칭; 없으면 WARN)
  5. 인용 [n] ↔ 참고문헌 항목 매칭 (참고문헌 섹션 있을 때만)

종료 코드: 0 = PASS (HIGH 0건), 1 = FAIL (HIGH ≥1건)
WARN은 출력만 하고 FAIL을 유발하지 않는다 (대상이 아직 없는 새 페이지일 수 있음).
"""
import re
import sys
import argparse
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:\|[^\]]*)?(?:#[^\]]*)?\]\]")
CITE_RE = re.compile(r"\[(\d+)\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S")


def parse_frontmatter(text):
    """간단한 frontmatter 파서. (fm_dict, body, fm_line_count) 반환."""
    if not text.startswith("---"):
        return {}, text, 0
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text, 0
    fm_text = text[4:end]
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    fm_line_count = text[: text.index(body)].count("\n") if body in text else 0
    return fm, body, fm_line_count


def collect_pages(content_dir):
    """content/ 내 .md 파일 stem 집합 (templates/, private/ 제외)."""
    pages = set()
    for p in Path(content_dir).rglob("*.md"):
        rel = p.relative_to(content_dir)
        if rel.parts[0] in ("templates", "private"):
            continue
        pages.add(p.stem)
    return pages


def verify_file(path, all_pages):
    """단일 파일 검증. (issues 리스트) 반환. issue=(severity, type, line, msg)."""
    issues = []
    text = path.read_text(encoding="utf-8")
    fm, body, fm_off = parse_frontmatter(text)

    # 1. frontmatter title
    if not fm.get("title"):
        issues.append(("HIGH", "frontmatter", 1, "title 필드 누락"))

    lines = body.split("\n")

    def abs_line(i):
        return fm_off + i + 1

    # 2. 코드 펜스 밸런스
    backtick = sum(1 for l in lines if l.lstrip().startswith("```"))
    tilde = sum(1 for l in lines if l.lstrip().startswith("~~~"))
    if backtick % 2 != 0:
        issues.append(("HIGH", "fence", 1, f"백틱 코드 펜스 불밸런스 ({backtick}개)"))
    if tilde % 2 != 0:
        issues.append(("HIGH", "fence", 1, f"물결 코드 펜스 불밸런스 ({tilde}개)"))

    # 펜스 내부가 아닌 헤딩 수집
    in_fence = False
    headings = []  # (line_idx, level, text)
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            hm = HEADING_RE.match(line)
            if hm:
                headings.append((i, len(hm.group(1)), line.strip()))

    # 3. 빈 섹션 — 헤딩과 다음 헤딩(또는 EOF) 사이에 본문 내용이 없으면.
    #    단, 다음 헤딩이 더 깊은 하위 섹션이면 컨테이너(정상)로 본다.
    for idx, (i, level_i, h) in enumerate(headings):
        start = i + 1
        if idx + 1 < len(headings):
            j, level_j, _ = headings[idx + 1]
            end = j
        else:
            end = len(lines)
            level_j = None
        has_content = any(
            l.strip() and not HEADING_RE.match(l)
            for l in lines[start:end]
        )
        if not has_content and not (level_j is not None and level_j > level_i):
            issues.append(("HIGH", "empty-section", abs_line(i), f"빈 섹션: {h}"))

    # 4. 위키링크 대상 존재
    for m in WIKILINK_RE.finditer(body):
        target = m.group(1).strip()
        if target and target not in all_pages:
            line_no = body[: m.start()].count("\n") + 1
            issues.append((
                "WARN", "wikilink", abs_line(line_no - 1),
                f"대상 없음(새 페이지일 수 있음): [[{target}]]",
            ))

    # 5. 인용 [n] ↔ 참고문헌 매칭 (참고문헌 섹션이 있을 때만)
    ref_start = None
    ref_end = None
    for i, line in enumerate(lines):
        if HEADING_RE.match(line) and "참고문헌" in line:
            ref_start = i + 1
        elif ref_start is not None and HEADING_RE.match(line):
            ref_end = i
            break
    if ref_start is not None:
        if ref_end is None:
            ref_end = len(lines)
        ref_text = "\n".join(lines[ref_start:ref_end])
        defined = {int(m.group(1)) for m in CITE_RE.finditer(ref_text)}
        body_text = "\n".join(lines[: ref_start - 1] + lines[ref_end:])
        used = {int(m.group(1)) for m in CITE_RE.finditer(body_text)}
        undefined = sorted(used - defined)
        if undefined:
            issues.append(("HIGH", "citation", 1, f"참고문헌에 없는 인용: {undefined}"))

    return issues


def main():
    ap = argparse.ArgumentParser(description="Quartz 위키 페이지 검증")
    ap.add_argument("path", help="검증할 .md 파일 또는 content 디렉토리")
    ap.add_argument(
        "--content-dir",
        default=None,
        help="위키링크 매칭 기준 디렉토리 (기본: path가 디렉토리면 그것, 파일면 ../content 추정)",
    )
    args = ap.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"오류: 경로 없음 — {target}", file=sys.stderr)
        return 2

    # content_dir 결정: 위키링크 대상 집합을 만들 기준
    if args.content_dir:
        content_dir = Path(args.content_dir)
    elif target.is_dir():
        content_dir = target
    else:
        # 파일이면 상위에서 content/ 찾기
        for parent in [target.parent, *target.parents]:
            if parent.name == "content":
                content_dir = parent
                break
        else:
            content_dir = target.parent

    all_pages = collect_pages(content_dir)

    if target.is_dir():
        files = [
            p for p in target.rglob("*.md")
            if "templates" not in p.relative_to(target).parts
            and "private" not in p.relative_to(target).parts
        ]
    else:
        files = [target]

    total_high = 0
    total_warn = 0
    for f in files:
        issues = verify_file(f, all_pages)
        high = [i for i in issues if i[0] == "HIGH"]
        warn = [i for i in issues if i[0] == "WARN"]
        total_high += len(high)
        total_warn += len(warn)
        status = "PASS" if not high else "FAIL"
        print(f"\n{'✅' if status == 'PASS' else '❌'} {status}  {f.name}")
        for sev, typ, line, msg in issues:
            mark = "❌" if sev == "HIGH" else "⚠️ "
            print(f"   {mark} L{line} [{typ}] {msg}")

    print(f"\n요약: {len(files)}개 파일, HIGH {total_high}건, WARN {total_warn}건")
    return 1 if total_high else 0


if __name__ == "__main__":
    sys.exit(main())
