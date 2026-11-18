"""Claude Code plugin Top 5 by installs -> claude-top5.json

Source: https://claude.com/plugins (official directory, listed in install order)
        and the "Installs" number on each https://claude.com/plugins/<slug> page.
Install command: `/plugin install {name}@claude-plugins-official`
                 (anthropics/claude-plugins-official README)

Usage: python update_claude_top5.py --out claude-top5.json
Runs weekly (Monday 06:00 KST) via .github/workflows/daily.yml
Videos are hand-picked only (VIDEO below); plugins without one show no video.
"""
import argparse, datetime, json, re, sys, urllib.request

BASE = 'https://claude.com/plugins'
UA = {'User-Agent': 'Mozilla/5.0 (claude-plugins-top5 daily updater)'}

# Korean two-line summaries (from the official descriptions). New entries fall back to the first English sentence - add them here.
KO = {
    'frontend-design': ['AI가 만든 티 나는 화면 대신, 목적과 대상에 맞는 디자인 방향부터 정하고 화면을 만들어요',
                        '대시보드·랜딩 페이지를 만들어 달라고 하면 자동으로 켜져요'],
    'superpowers': ['바로 코딩하지 않고 먼저 질문하고 계획부터 세우게 해요',
                    '테스트 먼저 작성(TDD), 체계적인 디버깅, 코드 리뷰까지 순서대로 진행해요'],
    'code-review': ['여러 검토 에이전트가 PR을 동시에 서로 다른 관점으로 검토해요',
                    '확신도가 높은 문제만 골라 GitHub에 남겨서 헛경보가 적어요'],
    'context7': ['라이브러리의 최신 버전 공식 문서와 예제를 가져와 답에 넣어요',
                 "요청에 'use context7'을 붙이면 옛날 API나 지어낸 코드가 줄어요"],
    'code-simplifier': ['최근에 고친 코드를 더 읽기 쉽고 일관되게 정리해 줘요',
                        '동작은 그대로 두고 구조만 다듬어요'],
    'playwright': ['웹사이트를 열고 클릭·입력·스크린샷까지 직접 해 보며 확인해요',
                   '배포 전에 화면 오류를 미리 잡을 때 좋아요'],
    'github': ['GitHub 이슈·PR·코드 검색을 Claude 안에서 바로 다뤄요',
               'PR 만들기와 리뷰 남기기까지 명령 한 번으로 해요'],
    'claude-md-management': ['프로젝트 기억 파일(CLAUDE.md)을 점검하고 최신으로 정리해요',
                             '오래되거나 틀린 안내가 남지 않게 관리해요'],
    'feature-dev': ['코드 탐색 → 설계 → 구현 → 검토 순서로 기능 개발을 진행해요',
                    '단계마다 전문 에이전트가 나눠 맡아요'],
    'ralph-loop': ['같은 작업을 끝날 때까지 AI가 혼자 반복해서 완성해요',
                   '자기 전에 걸어 두면 일어났을 때 결과가 나와 있어요'],
    'claude-code-setup': ['내 프로젝트를 보고 자동화할 부분(훅·스킬·MCP 등)을 알려 줘요',
                          '처음 세팅할 때 쓰면 좋아요'],
}


# YouTube videos per plugin (checked public + embeddable via oEmbed). Add new ones here.
VIDEO = {
    'frontend-design': ['Lj4ChneyDVg', 'How to Build Better UI With Claude Code'],
    'superpowers': ['yEzzBxhkUw4', 'The Claude Code Plugin Every Developer Must Learn (Superpowers)'],
    'context7': ['CG29OwYrXW0', 'Context7 MCP: Live Documentation in Claude Code'],
    'code-simplifier': ['puynahM0Wew', 'NEW Claude Code Plugin: Code Simplifier'],
}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode('utf-8', 'replace')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=5)
    a = ap.parse_args()

    listing = get(BASE)
    slugs = []
    for s in re.findall(r'/plugins/([a-z0-9][a-z0-9-]{2,})', listing):
        if s not in ('submit',) and s not in slugs:
            slugs.append(s)
    if len(slugs) < a.n:
        sys.exit('could not read plugin list (page structure may have changed)')

    items = []
    for s in slugs[:a.n * 2]:                       # listing order = install order; re-sort by the actual numbers
        page = get(BASE + '/' + s)
        m = re.search(r'>Installs</span><span[^>]*>([\d,]+)<', page)
        if not m:
            continue
        name = re.search(r'<title>([^<|]+)', page)
        desc = re.search(r'<meta name="description" content="([^"]*)"', page)
        en = (desc.group(1) if desc else '').strip()
        items.append({'slug': s, 'name': (name.group(1).strip() if name else s), 'installs': int(m.group(1).replace(',', '')),
                      'desc': KO.get(s) or [en.split('. ')[0][:90], ''], 'ko': s in KO,
                      'video': None,
                      'url': BASE + '/' + s, 'install': '/plugin install %s@claude-plugins-official' % s})
    items.sort(key=lambda x: -x['installs'])
    items = items[:a.n]
    for i, it in enumerate(items):
        it['rank'] = i + 1
        it['video'] = {'id': VIDEO[it['slug']][0], 'title': VIDEO[it['slug']][1]} if it['slug'] in VIDEO else None
    out = {'date': datetime.date.today().isoformat(), 'source': BASE, 'basis': '설치 수', 'items': items}
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('ok', out['date'], [(x['rank'], x['slug'], x['installs'], x['ko'], (x['video'] or {}).get('id')) for x in items])


if __name__ == '__main__':
    main()
