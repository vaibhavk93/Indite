"""The list pages of the Mac window, run in headless Chrome against made-up notes (skipped without Chrome).

Covers: search (words, quotes, curly quotes, accents, codes, symbols, other scripts), filters (chips, When, App, Review),
sort, group, windowed lists, our own menus, Meetings / Files / To do / Dictionary, find inside one transcript, the delete
choices and "How many to keep". The page is the real mac/ui/app.html with a stubbed bridge; the notes are invented, so
this never touches your data. The messages the page would send to Python are captured and checked too."""
import html as htmllib
import json
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHROME = next((p for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                           shutil.which("google-chrome") or "", shutil.which("chromium") or "") if p and Path(p).exists()), None)
pytestmark = pytest.mark.skipif(CHROME is None, reason="needs Chrome or Chromium")
sys.path.insert(0, str(ROOT / "mac"))
import store  # noqa: E402

NOW = time.time()
DAY = 86400


def note(i, text, ago=0, **kw):
    at = NOW - ago - i
    return {"id": repr(at), "at": at, "text": text, "seconds": 3, "took": 1, "where": "done", "app": "Notes", **kw}


def run(rows, steps, prefs=None):
    """Loads the page with these notes and runs the JS in `steps` (it fills R); returns R."""
    state = {"prefs": {**store.DEFAULTS, "views": {}, "ai": True, **(prefs or {})}, "history": sorted(rows, key=lambda r: -r["at"]), "hotkeys": {},
             "listening": True, "engine": "ready", "fixes": 0, "fixes_list": [], "ai_providers": {}, "ai_models": {}, "ai_catalog": {},
             "ai_status": {}, "ai_keys": {}, "ai_actions": {}, "ai_style_groups": {}, "ai_langs": [], "ai_cost_month": [0, 0, 0],
             "fix_counts": {}, "ai_busy": {}}
    page = (ROOT / "mac/ui/app.html").read_text()
    stub = ("<script>window.webkit={messageHandlers:{indite:{postMessage(m){(window.__sent=window.__sent||[]).push(JSON.parse(m))}}}};"
            "window.onerror=(m)=>{(window.__err=window.__err||[]).push(m)};</script>")
    probe = ("<script>(()=>{const R={},n=s=>document.querySelectorAll(s).length,"
             "vc=p=>(document.querySelector('.qbar[data-for='+(p||'home')+'] .vcount')||{textContent:''}).textContent.replace(/\\s+/g,' ').trim(),"
             "heads=s=>[...document.querySelectorAll((s||'#list')+' .daybar')].map(e=>e.firstChild.textContent.trim()),"
             "texts=s=>[...document.querySelectorAll((s||'#list')+' .row .text')].map(e=>e.textContent.trim()),"
             "sent=k=>(window.__sent||[]).filter(m=>m.action===k),"
             "menu=()=>[...document.querySelectorAll('.menu button[data-v], .menu button[data-w]')].map(b=>b.textContent.replace(/\\s+/g,' ').trim());"
             f"window.push({json.dumps(json.dumps(state))});go('home');try{{{steps}}}catch(e){{R.fatal=e.message+' @'+((e.stack||'').split('\\n')[1]||'')}}R.err=window.__err||[];document.title=JSON.stringify(R)}})()</script>")
    tmp = Path(__file__).with_name("_page_under_test.html")
    try:
        tmp.write_text(stub + page + probe)
        dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=8000", "--dump-dom", f"file://{tmp}"],
                             capture_output=True, text=True, timeout=120).stdout
    finally:
        tmp.unlink(missing_ok=True)
    return json.loads(htmllib.unescape(dom.split("<title>")[1].split("</title>")[0]))


# --------------------------------------------------------------------------------------------------- search
CODES = ["Please review the launch report today", "launch the report after review", "Ticket JIRA-123 is blocked by PROJ-45",
         "invoice from emergent.com for ₹4,500", "price is a+b (x) [y] \\path .* ? $5 ^caret", "mail <b>bold</b> & more",
         "naam hai Rahul, ticket #77 done", "कल मीटिंग है report भेजना", "Café meeting at the résumé desk",
         'he said "launch report" twice', "UPPER Case LAUNCH", "x" * 400 + " long"]


def test_search_words_quotes_codes_and_symbols():
    rows = [note(i, t) for i, t in enumerate(CODES)]
    queries = ["launch report", '"launch report"', "“launch report”", "‘launch report’", "«launch report»", '"launch', 'launch"', '""', '"',
               "JIRA-123", "jira-123", "PROJ", "emergent.com", "₹4,500", "4,500", "#77", "rahul,", "a+b", "(x)", "[y]", "\\path", ".*",
               "?", "$5", "^caret", "<b>", "&", "कल", "cafe", "café", "resume", "RESUME", "upper case", "launch  report", "  launch  ",
               "x" * 300, '"launch report" review', '"a b" "c d"', "zzzz", ""]
    r = run(rows, f"R.q=[];for(const q of {json.dumps(queries)}){{$('#q').value=q;searched();R.q.push([n('#list .row'),n('#list mark')])}}"
                  "$('#q').value='<b>';searched();R.noinject=n('#list .text b');R.shown=texts()[0];")
    got = dict(zip(queries, [x[0] for x in r["q"]]))
    assert r["err"] == []
    assert got["launch report"] == 3                                   # all words, any order
    assert got['"launch report"'] == 2 and got["“launch report”"] == 2 and got["«launch report»"] == 2   # a phrase, curly quotes too
    assert got["‘launch report’"] == 2                                 # single curly quotes keep a phrase as well
    assert got['"launch'] == got['launch"'] == 4                       # a lone quote is just a quote
    assert got['""'] == got['"'] == got[""] == 12                      # nothing to look for: everything
    assert got["JIRA-123"] == got["jira-123"] == 1 and got["PROJ"] == 1 and got["#77"] == 1   # codes, any capitals
    assert got["emergent.com"] == got["₹4,500"] == got["4,500"] == 1
    assert all(got[q] == 1 for q in ["a+b", "(x)", "[y]", "\\path", ".*", "?", "$5", "^caret", "<b>", "&"])   # symbols are plain text
    assert got["कल"] == 1                                              # other scripts
    assert got["cafe"] == got["café"] == got["resume"] == got["RESUME"] == 1   # accents and capitals do not matter
    assert got["upper case"] == 1 and got["launch  report"] == 3 and got["  launch  "] == 4
    assert got["x" * 300] == 1 and got['"launch report" review'] == 1
    assert got['"a b" "c d"'] == 0 and got["zzzz"] == 0
    assert r["noinject"] == 0 and r["shown"].startswith("mail <b>bold</b>")   # text is shown as text, never as markup
    assert all(m > 0 for q, (cnt, m) in zip(queries, r["q"]) if q in ("launch report", "JIRA-123", "cafe") and cnt)   # matches are marked


def test_search_best_match_and_sort_override_and_escape():
    rows = [note(0, "budget", ago=0), note(1, "budget budget review", ago=DAY), note(2, "review budget plan budget budget", ago=2 * DAY)]
    r = run(rows, """
      $('#q').value='budget';searched();R.best=texts();
      R.sortLabel=document.querySelector('.qbar[data-for=home] .vm[data-k=sort]').textContent;
      document.querySelector('.qbar[data-for=home] .vm[data-k=sort]').click();R.options=menu();
      [...document.querySelectorAll('.menu button[data-v]')].find(b=>b.dataset.v==='old').click();R.oldest=texts();
      $('#q').value='';searched();R.afterClear=document.querySelector('.qbar[data-for=home] .vm[data-k=sort]').textContent;
      $('#q').value='budget';searched();$('#q').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));R.escCleared=$('#q').value===''&&n('#list .row');
    """)
    assert r["err"] == []
    assert r["best"][0].startswith("review budget plan") and r["sortLabel"] == "Best match"   # most mentions first
    assert r["options"][0] == "Best match" and "Newest first" in r["options"]
    assert r["oldest"][0] == "review budget plan budget budget"                              # picked another sort: it follows it
    assert r["afterClear"] == "Newest first" and r["escCleared"] == 3                          # cleared: back to the saved sort; Esc clears


# --------------------------------------------------------------------------------------------------- filters
def test_filters_when_app_review_combine_and_clear():
    rows = [note(0, "a today", app="Slack", star=True), note(1, "b yesterday", ago=DAY, app="Chrome", where="copied"),
            note(2, "c lastweek", ago=5 * DAY, app="Slack", ai=[{"label": "x", "text": "answer", "at": 1}]),
            note(3, "d old", ago=40 * DAY, app="Chrome", todo="open"), note(4, "e ancient", ago=400 * DAY, app="Slack"),
            note(5, "f suggestions", ago=100, app="Slack", flags=[{"heard": "a", "want": "b"}]),
            note(6, "g fixed", ago=200, app="Notes", reviewed=[{"heard": "a", "want": "b", "how": "fix", "at": 1}]),
            note(7, "h always", ago=300, app="Notes", reviewed=[{"heard": "a", "want": "b", "how": "always", "at": 1}]),
            note(8, "i dismissed", ago=400, app="Notes", reviewed=[{"heard": "a", "want": "b", "how": "dismiss", "at": 1}])]
    r = run(rows, """
      const pick=(k,v)=>{document.querySelector('.qbar[data-for=home] .vm[data-k='+k+']').click();[...document.querySelectorAll('.menu button[data-v]')].find(b=>b.dataset.v===v).click()};
      R.total=vc();setView('home',{filter:'star'});R.star=vc();setView('home',{filter:'copied'});R.copied=vc();setView('home',{filter:'ai'});R.ai=vc();setView('home',{filter:'todo'});R.todo=vc();
      setView('home',{filter:'all'});
      pick('review','open');R.open=vc();pick('review','fix');R.fix=vc();pick('review','always');R.always=vc();pick('review','dismiss');R.dismiss=vc();
      R.reviewMenu=(()=>{document.querySelector('.qbar[data-for=home] .vm[data-k=review]').click();const m=menu();document.body.click();return m})();
      pick('review','any');
      pick('when','today');R.today=vc();pick('when','7d');R.week=vc();pick('when','30d');R.month30=vc();pick('when','year');R.year=vc();
      pick('when','any');pick('app','Slack');R.slack=vc();
      pick('when','7d');R.slackWeek=vc();R.onClasses=[...document.querySelectorAll('.qbar[data-for=home] .vm.on')].map(b=>b.dataset.k);
      document.querySelector('.qbar[data-for=home] [data-clear=home]').click();R.cleared=vc();R.clearedRows=n('#list .row');
      setView('home',{app:'Gone App',filter:'zzz',review:'zzz',when:'zzz'});R.stale=n('#list .row');
    """)
    assert r["err"] == []
    assert r["total"] == "" and r["star"] == "1 of 9 Clear" and r["copied"] == "1 of 9 Clear" and r["ai"] == "1 of 9 Clear" and r["todo"] == "1 of 9 Clear"
    assert (r["open"], r["fix"], r["always"], r["dismiss"]) == ("1 of 9 Clear",) * 4
    assert r["reviewMenu"][:5] == ["Any review state", "Has suggestions · 1", "Fixed · 1", "Always fix · 1", "Not a mistake · 1"]
    assert r["today"] == "5 of 9 Clear"                                  # five notes were made in the last few minutes
    assert r["month30"] == r["week"] and r["year"] == "8 of 9 Clear"     # the 400-day-old one is last year
    assert r["slack"] == "4 of 9 Clear"                                  # a, c, e, f
    assert r["slackWeek"] == "3 of 9 Clear"                              # a, c, f
    assert set(r["onClasses"]) == {"when", "app"}                        # a menu with a non-default choice looks pressed
    assert r["cleared"] == "" and r["clearedRows"] == 9                  # Clear puts everything back
    assert r["stale"] == 9                                               # saved choices that no longer exist are ignored, not fatal


# --------------------------------------------------------------------------------------------------- sort, group, window
def test_sort_group_and_windowing():
    rows = [note(i, " ".join(["w"] * (i % 7 + 1)), ago=(i // 5) * DAY, app=["Slack", "Chrome", "Chrome", "Notes"][i % 4]) for i in range(230)]
    rows += [note(900, "very old note", ago=500 * DAY)]
    r = run(rows, """
      R.first=[n('#list .row'),document.querySelector('#list .more-rows').textContent];
      document.querySelector('#list .more-rows').click();R.more=n('#list .row');
      setView('home',{sort:'old'});R.oldFirst=heads()[0];
      setView('home',{sort:'long',group:'none'});R.longHeads=heads().length;R.longFirst=texts()[0].split(' ').length;
      setView('home',{sort:'short',group:'none'});R.shortFirst=texts()[0].split(' ').length;
      setView('home',{sort:'new',group:'app'});R.appHeads=heads().slice(0,3);
      setView('home',{group:'date',sort:'new'});R.dateHeads=heads().slice(0,3);
      setView('home',{sort:'new'});R.afterChange=n('#list .row');
    """)
    assert r["err"] == []
    assert r["first"] == [100, "Show 100 more · 131 left"]                  # 231 notes: 100 drawn, the rest counted
    assert r["more"] == 200                                                 # "Show more" adds 100
    assert r["oldFirst"] == datetime.fromtimestamp(NOW - 500 * DAY).strftime("%B %Y")   # oldest group first, with its year
    assert r["longHeads"] == 0 and r["longFirst"] == 7 and r["shortFirst"] == 1          # no groups; longest and shortest first
    assert r["appHeads"] == ["Chrome"]                                      # biggest app group first (it fills the first 100 rows)
    assert r["dateHeads"][0] == "Today" and r["afterChange"] == 100         # changing a view starts the window over


def test_date_headings_read_like_a_person_would():
    rows = [note(0, "t", ago=60), note(1, "y", ago=DAY), note(2, "w", ago=4 * DAY), note(3, "old", ago=200 * DAY), note(4, "older", ago=800 * DAY)]
    r = run(rows, "R.h=heads();")
    h = r["h"]
    assert h[0] == "Today" and h[1] == "Yesterday" and h[2].split()[0] in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    assert h[-2] == datetime.fromtimestamp(NOW - 200 * DAY).strftime("%B %Y") and h[-1] == datetime.fromtimestamp(NOW - 800 * DAY).strftime("%B %Y")


# --------------------------------------------------------------------------------------------------- own menus
def test_toolbar_uses_our_menus_not_system_dropdowns():
    rows = [note(i, f"n{i}", ago=i * 40 * DAY, app="Slack") for i in range(5)]
    r = run(rows, """
      R.selects=n('.qbar select');R.buttons=[...document.querySelectorAll('.qbar[data-for=home] .vm')].map(b=>b.dataset.k);
      document.querySelector('.qbar[data-for=home] .vm[data-k=when]').click();
      R.open=n('.menu.vmenu');R.items=menu().slice(0,9);R.cur=document.querySelector('.menu .cur')?.textContent;
      R.monthsGrouped=[...document.querySelectorAll('.menu .mh')].map(e=>e.textContent);
      document.querySelector('.menu').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));R.closed=n('.menu');
      document.querySelector('.qbar[data-for=home] .vm[data-k=sort]').click();
      [...document.querySelectorAll('.menu button[data-v]')].find(b=>b.dataset.v==='long').click();
      R.sortText=document.querySelector('.qbar[data-for=home] .vm[data-k=sort]').textContent;R.saved=sent('pref').filter(m=>m.key==='views').pop().value.home;
    """)
    assert r["err"] == [] and r["selects"] == 0                              # no operating-system dropdowns in the toolbar
    assert r["buttons"] == ["when", "app", "review", "group", "sort"]
    assert r["open"] == 1 and r["items"][0] == "Any time" and r["cur"] == "Any time" and "A month" in r["monthsGrouped"] and r["closed"] == 0
    assert r["sortText"] == "Longest first" and r["saved"]["sort"] == "long"      # the choice is saved for next time


# --------------------------------------------------------------------------------------------------- other pages
def meeting(i, title, lines, ago=0, **kw):
    segs = [{"speaker": sp, "text": t, "start": j * 5.0, "end": j * 5.0 + 4} for j, (sp, t) in enumerate(lines)]
    return {"id": repr(NOW - ago - i), "at": NOW - ago - i, "kind": "meeting", "title": title, "text": "\n".join(f"{a}: {b}" for a, b in lines),
            "segments": segs, "seconds": 600 + i * 100, "took": 0, "where": "done", "app": "", "audio": 2, **kw}


def test_meetings_files_todo_dictionary():
    lines = [("You", f"line {k} about nothing") for k in range(12)] + [("Priya", "the pricing proposal is ready"), ("You", "ok send the pricing deck")]
    rows = [meeting(0, "Standup", [("You", "hello team"), ("Priya", "status update")], ago=60), meeting(1, "Pricing review", lines, ago=DAY, star=True),
            note(2, "an audio file about budgets", ago=2 * DAY, kind="file", title="call.m4a", seconds=900),
            note(3, "buy milk", todo="open"), note(4, "call the bank", todo="done", ago=DAY), note(5, "plain dictation")]
    r = run(rows, """
      go('meetings');R.m=n('#meet-list .row');
      $('#q').value='pricing';searched();R.mHit=n('#meet-list .row');R.mShown=[...document.querySelectorAll('#meet-list .line:not(.hide) .text')].map(e=>e.textContent);R.mMarks=n('#meet-list mark');R.mCount=vc('meetings');
      $('#q').value='';searched();setView('meetings',{filter:'star'});R.mStar=n('#meet-list .row');setView('meetings',{filter:'all',sort:'title'});R.mTitleFlat=heads('#meet-list').length;R.mTitle=[...document.querySelectorAll('#meet-list .title')].map(e=>e.textContent.trim());
      setView('meetings',{sort:'long'});R.mLong=[...document.querySelectorAll('#meet-list .title')].map(e=>e.textContent.trim());
      go('files');R.f=n('#file-list .row');$('#q').value='budgets';searched();R.fHit=n('#file-list .row');$('#q').value='zzz';searched();R.fNone=document.querySelector('#file-list .empty h3').textContent;
      $('#q').value='';go('todo');R.t=n('#todo-list .row');R.tChips=document.querySelector('.qbar[data-for=todo] .chips').textContent.replace(/\\s+/g,' ');
      setView('todo',{filter:'done'});R.tDone=n('#todo-list .row');setView('todo',{filter:'open'});R.tOpen=n('#todo-list .row');
      setView('todo',{filter:'all'});$('#q').value='milk';searched();R.tSearch=n('#todo-list .row');$('#q').value='nothing';searched();R.tNone=document.querySelector('#todo-list .empty h3').textContent;
    """)
    assert r["err"] == []
    assert r["m"] == 2 and r["mHit"] == 1 and r["mCount"] == "1 of 2 Clear"
    assert any("pricing" in t for t in r["mShown"]) and r["mMarks"] >= 2           # a match deep in a meeting is shown, not hidden
    assert r["mStar"] == 1 and r["mTitle"] == ["Pricing review", "Standup"] and r["mTitleFlat"] == 0   # Title A–Z: one plain list, not date groups
    assert r["mLong"][0] == "Pricing review"                                       # the longer recording first
    assert r["f"] == 1 and r["fHit"] == 1 and r["fNone"] == "Nothing matches"
    assert r["t"] == 2 and "Open · 1" in r["tChips"] and "Done · 1" in r["tChips"]
    assert (r["tDone"], r["tOpen"], r["tSearch"]) == (1, 1, 1) and r["tNone"] == "Nothing matches"


def test_dictionary_search_sort_letters_and_empty():
    fixes = [[f"{c}word", f"Right {c}"] for c in "bcdefghijklmnopqrstuvwxyz"] + [["alpha", "Zeta"], ["jira", "Jira"], ["Éclair", "Cake"], ["omega", "Alpha"], ["x y", "XY"], ["kappa", "K"], ["sigma", "S"]]
    r = run([note(0, "x")], """
      S.fixes_list=%s;go('dict');R.n=n('#dict-list .dict-row');R.letters=n('#dict-list .daybar');
      $('#q').value='jira';searched();R.jira=n('#dict-list .dict-row');R.cnt=vc('dict');
      $('#q').value='eclair';searched();R.accent=n('#dict-list .dict-row');
      $('#q').value='cake éclair';searched();R.two=n('#dict-list .dict-row');
      $('#q').value='';searched();setView('dict',{sort:'meant'});R.meant=document.querySelector('#dict-list .dict-row .w').textContent;
      setView('dict',{sort:'new'});R.newest=document.querySelector('#dict-list .dict-row .h').textContent;
      setView('dict',{sort:'old'});R.oldest=document.querySelector('#dict-list .dict-row .h').textContent;
      setView('dict',{sort:'az'});$('#q').value='nope';searched();R.none=document.querySelector('#dict-list .empty h3').textContent;
    """ % json.dumps(fixes))
    assert r["err"] == [] and r["n"] == 32 and r["letters"] >= 20            # over 30 entries: letter headings appear
    assert r["jira"] == 1 and r["cnt"] == "1 of 32 Clear" and r["accent"] == 1 and r["two"] == 1
    assert r["meant"] == "Alpha" and r["newest"] == "sigma" and r["oldest"] == "bword" and r["none"] == "Nothing matches"


# --------------------------------------------------------------------------------------------------- find in one transcript
def test_find_inside_one_long_transcript():
    lines = [("You" if k % 2 else "Priya", f"filler sentence number {k} nothing special") for k in range(60)]
    lines[7] = ("Priya", "the Pricing proposal needs a second look")
    lines[31] = ("You", "yes the pricing proposal is final")
    lines[50] = ("Priya", "send the proposal about hiring")
    m = meeting(0, "Long call", lines, seconds=3600)
    r = run([m], """
      openDrawer(S.history[0].id,'listen');
      R.bar=n('#pfq');R.lines=n('#drawer .pline');
      const q=$('#pfq');q.value='pricing proposal';q.dispatchEvent(new Event('input'));
      R.hits=n('#drawer .pline.fhit');R.count=$('#pfc').textContent;R.cur=n('#drawer .pline.fcur');
      R.hl=(window.CSS&&CSS.highlights&&CSS.highlights.has('find'))?[...CSS.highlights.get('find')].length:'n/a';
      const first=document.querySelector('#drawer .pline.fcur').dataset.s;$('#pfn').click();R.next=$('#pfc').textContent;R.moved=document.querySelector('#drawer .pline.fcur').dataset.s!==first;
      q.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',shiftKey:true}));R.prev=$('#pfc').textContent;
      q.value='"proposal about"';q.dispatchEvent(new Event('input'));R.phrase=$('#pfc').textContent;
      q.value='zzzz';q.dispatchEvent(new Event('input'));R.none=$('#pfc').textContent;R.noneHits=n('#drawer .pline.fhit');
      q.value='priya';q.dispatchEvent(new Event('input'));R.speaker=$('#pfc').textContent;
      q.value='';q.dispatchEvent(new Event('input'));R.cleared=[$('#pfc').textContent,n('#drawer .pline.fhit')];
    """)
    assert r["err"] == [] and r["bar"] == 1 and r["lines"] == 60
    assert r["hits"] == 2 and r["count"] == "1 of 2 lines" and r["cur"] == 1     # the lines that have both words
    assert r["hl"] in ("n/a", 4) or r["hl"] >= 2                                  # words marked (when the browser supports it)
    assert r["next"] == "2 of 2 lines" and r["moved"] and r["prev"] == "1 of 2 lines"
    assert r["phrase"] == "1 of 1 line" and r["none"] == "No lines" and r["noneHits"] == 0
    assert r["speaker"].endswith("lines") and int(r["speaker"].split(" of ")[1].split()[0]) == 31    # a speaker's name searches too (30 turns + the edited one)
    assert r["cleared"] == ["", 0]


# --------------------------------------------------------------------------------------------------- delete choices
def test_delete_asks_what_to_delete():
    with_sound = note(0, "has sound", audio=1)
    no_sound = note(1, "no sound")
    a_file = note(2, "a file", kind="file", audio=1, title="x.m4a")
    words_gone = note(3, "", audio=1, text_deleted=True)
    mtg = meeting(4, "Call", [("You", "hi")])
    r = run([with_sound, no_sound, a_file, words_gone, mtg], """
      const by=t=>S.history.find(x=>x.text===t||x.title===t);
      askDelete(document.body,by('has sound'));R.menu=menu();document.querySelector('.menu button[data-w=audio]').click();
      askDelete(document.body,by('has sound'));document.querySelector('.menu button[data-w=text]').click();
      askDelete(document.body,by('has sound'));document.querySelector('.menu button[data-w=both]').click();
      R.sent=sent('delete').map(m=>m.what);
      askDelete(document.body,by('no sound'));R.noSoundAsks=n('.menu');R.noSoundSent=sent('delete').pop().what;
      askDelete(document.body,by('call.m4a')||by('x.m4a'));R.fileAsks=n('.menu');R.fileSent=sent('delete').pop().what;
      askDelete(document.body,S.history.find(x=>x.text_deleted));R.goneMenu=menu();
      askDelete(document.body,by('Call'));R.meetingMenu=menu();document.body.click();
      R.undoToast=document.querySelector('.toast')?.textContent||'';
    """)
    assert r["err"] == []
    assert r["menu"] == ["The note and its recordingEverything about it", "The recording onlyKeeps the words and frees the disk space",
                         "The words onlyKeeps the recording; the note stays as sound"] or len(r["menu"]) == 3
    assert r["sent"] == ["audio", "text", "both"]                              # each choice reaches Python as asked
    assert r["noSoundAsks"] == 0 and r["noSoundSent"] == "both"                # nothing to choose between: deleted at once, with Undo
    assert r["fileAsks"] == 0 and r["fileSent"] == "both"                      # a transcribed file's original is never touched
    assert len(r["goneMenu"]) == 2 and len(r["meetingMenu"]) == 3              # words already deleted: no second "words only"


def test_deleted_words_say_so_everywhere():
    gone = note(0, "", audio=1, text_deleted=True)
    r = run([gone], "R.row=texts()[0];openDrawer(S.history[0].id,'listen');R.listen=document.querySelector('#drawer .pline.whole')?.textContent.trim();")
    assert r["err"] == [] and "Words deleted" in r["row"] and "Words deleted" in r["listen"]


# --------------------------------------------------------------------------------------------------- how many to keep
def keep_rows(n):
    return [note(i, f"d{i}") for i in range(n)]


def test_how_many_to_keep_asks_before_deleting():
    steps = """
      go('settings');[...document.querySelectorAll('*')].find(e=>e.children.length==0&&e.textContent.trim()==='Privacy').click();
      const segs=()=>[...document.querySelectorAll('#set-history_cap button')];
      R.labels=segs().map(b=>b.textContent);R.current=segs().find(b=>b.getAttribute('aria-checked')==='true').textContent;R.why=$('#cap-why').textContent;
      segs()[2].click();R.bigSent=sent('pref').filter(m=>m.key==='history_cap').map(m=>m.value);R.warnHidden=$('#cap-warn').hidden;
      segs()[0].click();R.smallSent=sent('pref').filter(m=>m.key==='history_cap').map(m=>m.value);
    """
    r = run(keep_rows(60), steps, prefs={"history_cap": 5000})
    assert r["err"] == [] and r["labels"] == ["Newest 500", "Newest 5,000", "Everything"] and r["current"] == "Newest 5,000"
    assert r["bigSent"] == [0] and r["warnHidden"] is True                       # more room: applied at once
    assert r["smallSent"] == [0, 500]                                            # 60 notes fit in 500: no warning, applied
    r = run(keep_rows(700), steps.replace("segs()[0].click();", "segs()[0].click();R.warn=$('#cap-warn').hidden;R.warnText=$('#cap-warn-t').textContent;$('#cap-no').click();R.afterNo=sent('pref').filter(m=>m.key==='history_cap').length;segs()[0].click();$('#cap-yes').click();"),
            prefs={"history_cap": 5000})
    assert r["warn"] is False and r["warnText"].startswith("200 older dictations would be deleted")    # 700 kept, limit 500
    assert r["afterNo"] == 1                                                    # "Keep them": nothing was sent (only the earlier Everything)
    assert r["smallSent"] == [0, 500]                                           # "Delete them": now it is sent
    r = run(keep_rows(10), steps, prefs={"keep_history": False})
    assert r["err"] == [] and "Save my dictations" in r["why"]                  # saving is off: the choice is disabled and says why


# --------------------------------------------------------------------------------------------------- settings: model, effort, rupees
def test_settings_model_effort_and_rupees():
    from models import catalog  # noqa: PLC0415
    cases = {
        "login": dict(ai_provider="claude", claude_model="haiku", ai_effort="low"),
        "api_no_effort": dict(ai_provider="anthropic", ai_model="claude-haiku-4-5"),
        "openai": dict(ai_provider="openai", ai_model="gpt-5"),
        "inr": dict(ai_provider="claude", cost_currency="INR", usd_inr=85.5),
        "inr_norate": dict(ai_provider="claude", cost_currency="INR", usd_inr=0),
    }
    out = {}
    for name, prefs in cases.items():
        out[name] = run([note(0, "x")], """
          S.ai_catalog=%s;go('settings');[...document.querySelectorAll('*')].find(e=>e.children.length==0&&e.textContent.trim()==='AI').click();draw();
          const q=s=>document.querySelector(s);R.effort=[...q('#set-ai_effort').options].map(o=>o.value);R.effOff=q('#ai-effort-row').classList.contains('off');
          R.inrOff=q('#inr-row').classList.contains('off');R.money=[money(0.000177),money(1.2)];R.refresh=q('#ai-models-refresh').disabled;
        """ % json.dumps(catalog()), prefs={"ai": True, **prefs})
    assert all(v["err"] == [] for v in out.values())
    assert out["login"]["effort"] == ["", "low", "medium", "high", "xhigh", "max"] and out["login"]["effOff"] is False
    assert out["api_no_effort"]["effOff"] is True and out["openai"]["effOff"] is True      # no effort setting: disabled with a reason
    assert out["inr"]["money"] == ["₹0.0151", "₹102.60"] and out["inr"]["inrOff"] is False
    assert out["inr_norate"]["money"] == ["$0.0002", "$1.20"]                              # no rate typed: never a guessed one
    assert out["login"]["inrOff"] is True and out["login"]["money"][0] == "$0.0002"
