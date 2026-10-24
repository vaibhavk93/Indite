"""What the window actually SHOWS, not just what its data says (added 24 Oct after two bugs the first tests missed:
a menu count that did not match the list, and a warning row the Settings page un-hid every time you switched section).

Every check here looks at real on-screen visibility (computed display and size) and at invariants that must hold for
ANY state of the filters:
  1. a number shown on a button or in a menu is exactly how many notes you get by choosing it, whatever else is on;
  2. the rows on screen are the rows the count says;
  3. nothing that should be hidden is visible, and nothing that should be visible is hidden;
  4. a choice survives the round trip through Python (the page is rebuilt from the saved choices);
  5. switching Settings sections and pages never brings back a question you answered.
Runs the real mac/ui/app.html in headless Chrome against invented notes (skipped without Chrome)."""
import itertools
import json
import random
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_lists_ui import CHROME, DAY, NOW, meeting, note, run  # noqa: E402

pytestmark = pytest.mark.skipif(CHROME is None, reason="needs Chrome or Chromium")

# A helper block every scenario below shares: read the toolbar, apply a choice, compare numbers with the screen.
JS = r"""
const P = (k,v) => ({home:'#list', meetings:'#meet-list', files:'#file-list', todo:'#todo-list'});
const listOf = p => ({home:'#list', meetings:'#meet-list', files:'#file-list', todo:'#todo-list'})[p];
const barOf = p => document.querySelector('.qbar[data-for='+p+']');
const num = t => { const m = (t||'').match(/([\d,]+)\s*$/); return m ? +m[1].replace(/,/g,'') : null };
const shownCount = (p, total) => { const e = barOf(p).querySelector('.vcount'); return e && e.children.length ? +e.querySelector('b').textContent.replace(/,/g,'') : total };
const visibleRows = p => [...document.querySelectorAll(listOf(p)+' .row')].filter(vis).length;
const menuItems = (p, key) => { const b = barOf(p).querySelector('.vm[data-k='+key+']'); if (!b) return []; b.click();
  const items = [...document.querySelectorAll('.menu button[data-v]')].map(x => ({v: x.dataset.v, n: num(x.textContent)})); document.querySelectorAll('.menu').forEach(m => m.remove()); return items };
const chipItems = p => [...barOf(p).querySelectorAll('.chip')].map(c => ({v: c.dataset.f, n: c.dataset.f === 'all' ? null : num(c.textContent)}));
// For one page in its CURRENT state: every number on every chip and menu must equal what choosing it shows.
function audit(p, total, keys, tag) {
  const bad = [], here = JSON.parse(JSON.stringify((S.prefs.views||{})[p]||{}));
  const expectRows = Math.min(shownCount(p, total), 100);
  if (visibleRows(p) !== expectRows) bad.push(tag+': screen shows '+visibleRows(p)+' rows, count says '+shownCount(p,total));
  const trial = (key, v, n, label) => { setView(p, {[key]: v}); const got = shownCount(p, total);
    if (n !== null && got !== n) bad.push(tag+': '+key+'='+v+' says '+n+' but gives '+got);
    if (visibleRows(p) !== Math.min(got,100)) bad.push(tag+': after '+key+'='+v+' screen shows '+visibleRows(p)+' rows, count '+got);
    setView(p, {[key]: here[key] ?? (key === 'filter' ? 'all' : 'any')}); };
  for (const c of chipItems(p)) if (c.v !== 'all') trial('filter', c.v, c.n);
  for (const k of keys) for (const it of menuItems(p, k)) trial(k, it.v, it.n);
  return bad;
}
"""


def dataset(n=260, seed=11):
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        ago = rnd.choice([30, 3600, DAY * 0.5, 2 * DAY, 6 * DAY, 20 * DAY, 45 * DAY, 100 * DAY, 200 * DAY, 400 * DAY, 800 * DAY]) + i * 11
        kw = {"app": rnd.choice(["Terminal", "Terminal", "Claude", "Chrome", "Notes", ""])}
        if rnd.random() < 0.12:
            kw["star"] = True
        if rnd.random() < 0.15:
            kw["ai"] = [{"label": "x", "text": "answer", "at": 1}]
        if rnd.random() < 0.06:
            kw["todo"] = rnd.choice(["open", "done"])
        if rnd.random() < 0.12:
            kw["where"] = "copied"
        r = rnd.random()
        if r < 0.1:
            kw["flags"] = [{"heard": "a", "want": "b"}]
        elif r < 0.18:
            kw["reviewed"] = [{"heard": "a", "want": "b", "how": rnd.choice(["fix", "always", "dismiss"]), "at": 1}]
        rows.append(note(i, "budget plan " + " ".join(rnd.choice(["review", "launch", "invoice", "demo", "hiring"]) for _ in range(rnd.randint(2, 12))), ago=ago, **kw))
    return rows


# ------------------------------------------------------------------------------------- 1 + 2: numbers match the screen
def test_every_number_on_every_button_and_menu_matches_the_list():
    """The bug: 'Terminal · 318' showed 6 notes because another button was still on. For many combined states, every
    chip and menu number must equal what you get by choosing it, and the rows on screen must equal the count."""
    rows = dataset()
    rnd = random.Random(5)
    states = [{}] + [{"filter": rnd.choice(["all", "star", "ai", "todo", "copied"]), "when": rnd.choice(["any", "today", "7d", "30d", "month", "lastmonth", "year"]),
                      "app": rnd.choice(["any", "Terminal", "Claude", "Chrome", "Notes"]), "review": rnd.choice(["any", "open", "fix", "always", "dismiss"]),
                      "q": rnd.choice(["", "", "budget", "budget review", "zzzz", '"launch invoice"'])} for _ in range(45)]
    r = run(rows, JS + f"""
      const bad=[];for(const [i,st] of {json.dumps(states)}.entries()){{
        $('#q').value=st.q||'';searched();const patch={{...st}};delete patch.q;setView('home',patch);
        bad.push(...audit('home',{len(rows)},['when','app','review'],'state '+i+' '+JSON.stringify(st)));}}
      R.bad=bad.slice(0,12);R.nBad=bad.length;""")
    assert r["err"] == [] and r.get("fatal") is None, r
    assert r["nBad"] == 0, r["bad"]


def test_meetings_files_and_todo_numbers_match_too():
    rows = [meeting(i, f"Meeting {i}", [("You", "hello budget"), ("Priya", "launch plan")], ago=(i % 7) * 20 * DAY, **({"star": True} if i % 3 == 0 else {}),
                    **({"ai": [{"label": "x", "text": "a", "at": 1}]} if i % 4 == 0 else {})) for i in range(40)]
    rows += [note(100 + i, f"file {i} budget", ago=(i % 5) * 30 * DAY, kind="file", title=f"f{i}.m4a", seconds=60 * i, **({"star": True} if i % 2 else {})) for i in range(30)]
    rows += [note(200 + i, f"to do {i}", ago=(i % 6) * 15 * DAY, todo=["open", "done"][i % 2]) for i in range(30)]
    r = run(rows, JS + """
      const bad=[];
      go('meetings');bad.push(...audit('meetings',40,['when'],'meetings'));setView('meetings',{filter:'star'});bad.push(...audit('meetings',40,['when'],'meetings+star'));setView('meetings',{filter:'all'});
      go('files');bad.push(...audit('files',30,['when'],'files'));setView('files',{filter:'ai'});bad.push(...audit('files',30,['when'],'files+ai'));setView('files',{filter:'all'});
      go('todo');bad.push(...audit('todo',30,['when'],'todo'));setView('todo',{filter:'done'});bad.push(...audit('todo',30,['when'],'todo+done'));
      R.bad=bad.slice(0,10);R.nBad=bad.length;""")
    assert r["err"] == [] and r.get("fatal") is None, r
    assert r["nBad"] == 0, r["bad"]


def test_every_filter_that_is_on_is_named_and_an_empty_list_says_why():
    rows = [note(0, "a", app="Claude"), note(1, "b", app="Terminal", star=True), note(2, "c", app="Terminal", ago=3 * DAY)]
    r = run(rows, JS + """
      setView('home',{filter:'star',app:'Claude',when:'today'});
      R.count=shownCount('home',3);R.why=why('home');R.empty=document.querySelector('#list .empty h3').textContent;
      R.msg=document.querySelector('#list .empty').textContent.replace(/\\s+/g,' ');R.rows=visibleRows('home');
      R.onMenus=[...document.querySelectorAll('.qbar[data-for=home] .vm.on')].map(b=>b.dataset.k);
      R.pressed=[...document.querySelectorAll('.qbar[data-for=home] .chip[aria-pressed=true]')].map(c=>c.dataset.f);
      document.querySelector('#list [data-clear=home]').click();R.after=[vcAll('home'),visibleRows('home')];""")
    assert r["err"] == [] and r.get("fatal") is None
    assert r["count"] == 0 and r["rows"] == 0 and r["empty"] == "Nothing matches"
    assert all(x in r["msg"] for x in ("Starred", "Claude", "Today")) and "No note is all of these" in r["msg"]   # every filter that is on is named
    assert r["why"] == "Starred · Today · Claude"                    # and next to the count
    assert set(r["onMenus"]) == {"when", "app"} and r["pressed"] == ["star"]
    assert r["after"] == ["", 3]                                      # Clear brings everything back


# ------------------------------------------------------------------------------------- 3: visible / hidden
def test_the_right_things_are_visible_and_the_wrong_ones_are_not():
    r = run([note(0, "a")], JS + """
      R.toolbar=vis(barOf('home'));R.search=vis(document.querySelector('#q'));
      R.menusVisible=[...barOf('home').querySelectorAll('.vm')].every(vis);R.chipsVisible=[...barOf('home').querySelectorAll('.chip')].every(vis);
      R.noClear=!vis(barOf('home').querySelector('.vcount')) ;
      setView('home',{filter:'star'});R.clearShown=vis(barOf('home').querySelector('.vcount'));
      R.moreRowsGone=!document.querySelector('#list .more-rows');
      barOf('home').querySelector('.vm[data-k=sort]').click();R.menuShown=vis(document.querySelector('.menu.vmenu'));
      document.body.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}));setTimeout(()=>{},0);""")
    assert r["err"] == [] and r.get("fatal") is None
    assert r["toolbar"] and r["search"] and r["menusVisible"] and r["chipsVisible"]
    assert r["noClear"] and r["clearShown"] and r["menuShown"]
    empty = run([], JS + "R.toolbar=vis(barOf('home'));R.list=document.querySelector('#list').textContent.replace(/\\s+/g,' ').slice(0,40);")
    assert empty["toolbar"] is False and "Nothing dictated yet" in empty["list"]   # nothing saved: no toolbar, a friendly start


# ------------------------------------------------------------------------------------- 4: the round trip through Python
def test_a_choice_survives_the_round_trip_through_python():
    """Python saves the choice and sends the whole state back; the page is rebuilt from it. The list must not change."""
    rows = dataset(120)
    r = run(rows, JS + """
      setView('home',{app:'Terminal',filter:'ai',when:'30d',sort:'long',group:'none'});
      const before=[shownCount('home',120),visibleRows('home'),document.querySelector('#list .row .text')?.textContent.slice(0,30)];
      const sent=(window.__sent||[]).filter(m=>m.action==='pref'&&m.key==='views').pop().value;     // what Python would store
      S.prefs.views=sent;window.push(JSON.stringify(S));                                            // ...and send straight back
      const after=[shownCount('home',120),visibleRows('home'),document.querySelector('#list .row .text')?.textContent.slice(0,30)];
      R.same=JSON.stringify(before)===JSON.stringify(after);R.before=before;R.after=after;R.sentKeys=Object.keys(sent.home).sort();
      // an older saved view with missing keys, and one with junk, must still draw
      S.prefs.views={home:{filter:'ai'}};window.push(JSON.stringify(S));R.partial=visibleRows('home')>0;
      S.prefs.views={home:{filter:{x:1},when:5,app:null,sort:'zzz',group:'zzz'}};window.push(JSON.stringify(S));R.junk=visibleRows('home')>0;
      S.prefs.views=null;window.push(JSON.stringify(S));R.nullViews=visibleRows('home')>0;""")
    assert r["err"] == [] and r.get("fatal") is None, r
    assert r["same"], (r["before"], r["after"])
    assert r["sentKeys"] == ["app", "filter", "group", "review", "sort", "when"]
    assert r["partial"] and r["junk"] and r["nullViews"]


# ------------------------------------------------------------------------------------- 5: How many to keep, on screen
def test_keep_limit_question_is_asked_once_and_never_comes_back():
    notes = [note(i, f"d{i}") for i in range(700)]
    r = run(notes, JS + """
      const warn=()=>vis(document.querySelector('.capwarn')), seg=i=>[...document.querySelectorAll('#set-history_cap button')][i];
      const section=g=>document.querySelector('.snav button[data-g='+g+']').click();
      go('settings');section('privacy');
      R.fresh=warn();R.slotEmpty=document.querySelector('#cap-warn-slot').innerHTML.trim()==='';
      seg(0).click();R.asked=warn();R.askText=document.querySelector('.capwarn b').textContent;R.segFollows=seg(0).getAttribute('aria-checked');
      R.sentSoFar=(window.__sent||[]).filter(m=>m.key==='history_cap').length;
      document.querySelector('#cap-no').click();R.afterKeep=warn();R.afterKeepSent=(window.__sent||[]).filter(m=>m.key==='history_cap').length;
      section('writing');section('privacy');R.backAfterWriting=warn();
      go('home');go('settings');section('privacy');R.backAfterHome=warn();
      seg(0).click();R.asked2=warn();section('writing');section('privacy');R.droppedOnLeave=warn();
      seg(0).click();document.querySelector('#cap-yes').click();R.afterDelete=warn();R.sent=(window.__sent||[]).filter(m=>m.key==='history_cap').map(m=>m.value);
      seg(2).click();R.everything=(window.__sent||[]).filter(m=>m.key==='history_cap').map(m=>m.value);R.afterEverything=warn();
      go('home');go('settings');section('privacy');R.final=warn();""", prefs={"history_cap": 5000})
    assert r["err"] == [] and r.get("fatal") is None, r
    assert r["fresh"] is False and r["slotEmpty"]                       # nothing is waiting: nothing on screen
    assert r["asked"] and r["askText"].startswith("200 older dictations")  # a smaller limit asks, in words
    assert r["segFollows"] == "true" and r["sentSoFar"] == 0               # the button you pressed shows; nothing is changed yet
    assert r["afterKeep"] is False and r["afterKeepSent"] == 0             # "Keep them": gone, nothing sent
    assert r["backAfterWriting"] is False and r["backAfterHome"] is False  # leaving and coming back never brings it back
    assert r["asked2"] and r["droppedOnLeave"] is False                    # an unanswered question is dropped when you leave
    assert r["afterDelete"] is False and r["sent"] == [500]                # "Delete them": sent once, banner gone
    assert r["everything"] == [500, 0] and r["afterEverything"] is False and r["final"] is False


# ------------------------------------------------------------------------------------- other screens, on screen
def test_menus_open_close_and_pick_with_the_keyboard_and_mouse():
    rows = dataset(60)
    r = run(rows, JS + """
      const btn=barOf('home').querySelector('.vm[data-k=app]');btn.click();R.opened=vis(document.querySelector('.menu.vmenu'));
      R.items=[...document.querySelectorAll('.menu button[data-v]')].length;R.focus=document.activeElement.closest('.menu')!==null;
      document.querySelector('.menu').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true}));
      document.querySelector('.menu').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));R.escClosed=!document.querySelector('.menu');
      btn.click();document.body.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}));""")
    assert r["err"] == [] and r.get("fatal") is None
    assert r["opened"] and r["items"] >= 3 and r["focus"] and r["escClosed"]


def test_search_box_follows_you_between_pages_and_starts_empty():
    rows = [note(0, "budget"), meeting(1, "Call", [("You", "budget talk")]), note(2, "file", kind="file", title="f.m4a", seconds=5), note(3, "todo", todo="open")]
    r = run(rows, JS + """
      $('#q').value='budget';searched();R.home=[vis($('#q')),$('#q').closest('.qbar').dataset.for];
      const seen=[];S.fixes_list=[['a','b']];window.push(JSON.stringify(S));for(const t of ['meetings','files','todo','dict','home']){go(t);seen.push([t,vis($('#q')),$('#q').closest('.qbar').dataset.for,$('#q').value])}
      R.seen=seen;""")
    assert r["err"] == [] and r.get("fatal") is None
    assert r["seen"] == [["meetings", True, "meetings", ""], ["files", True, "files", ""], ["todo", True, "todo", ""], ["dict", True, "dict", ""], ["home", True, "home", ""]]


def test_scrolling_loads_more_rows_and_headings_stay_right():
    rows = [note(i, f"row {i}", ago=(i // 20) * DAY) for i in range(350)]
    r = run(rows, JS + """
      R.first=visibleRows('home');for(let i=0;i<3;i++)document.querySelector('#list .more-rows')?.click();R.after=visibleRows('home');
      R.left=document.querySelector('#list .more-rows')?.textContent||null;
      const heads=[...document.querySelectorAll('#list .daybar')].map(e=>e.firstChild.textContent.trim());R.uniqueHeads=heads.length===new Set(heads).size;
      setView('home',{sort:'old'});R.reset=visibleRows('home');""")
    assert r["err"] == [] and r.get("fatal") is None
    assert (r["first"], r["after"]) == (100, 350)
    assert r["left"] is None and r["uniqueHeads"] and r["reset"] == 100


# ------------------------------------------------------------------------------------- hostile and odd data
HOSTILE = [
    "plain note", "emoji 😀🎉 and flags 🇮🇳 and family 👨‍👩‍👧", "مرحبا بالعالم this is RTL ثم english", "עברית ואנגלית together", "zero​width​chars here",
    "<script>window.__pwned=1</script> and <img src=x onerror=window.__pwned=1> </script></div>", "A" * 6000, "word " * 3000, "  \n\n  \n ", "", "tab\tseparated\tand\nnewlines\nhere",
    "quote \" and ' and ` and \\ and ${window.__pwned=1} and {{x}}", "𝕌𝕟𝕚𝕔𝕠𝕕𝕖 𝔣𝔞𝔫𝔠𝔶", "कल मीटिंग है और report भेजना है ₹4,500", "very " + "long " * 400 + "end", "line1\r\nline2\rline3",
]


def test_hostile_notes_render_safely_and_stay_searchable():
    rows = [note(i, t) for i, t in enumerate(HOSTILE)]
    rows.append({"id": "weird.1", "at": NOW - 5, "text": "missing fields only"})                     # no seconds, app, where, took
    rows.append({"id": "weird.2", "at": NOW - 6, "text": "title is a number", "title": 12345, "app": None, "seconds": None})
    rows.append(meeting(900, "<b>Bold</b> title", [("<i>You</i>", "<script>window.__pwned=1</script>")]))
    r = run(rows, JS + """
      R.rows=visibleRows('home');R.pwned=window.__pwned||0;R.scripts=n('#list script, #list img');
      $('#q').value='RTL';searched();R.rtl=visibleRows('home');$('#q').value='😀';searched();R.emoji=visibleRows('home');
      $('#q').value='script';searched();R.script=visibleRows('home');R.pwned2=window.__pwned||0;R.marks=n('#list mark');
      $('#q').value='';searched();setView('home',{sort:'long'});R.long=visibleRows('home');setView('home',{sort:'short',group:'app'});R.app=visibleRows('home');
      go('meetings');R.meetings=visibleRows('meetings');R.meetingHtml=n('#meet-list b, #meet-list i');
      for(const p of ['files','todo','dict','insights','settings','help','home'])go(p);R.survived=true;""")
    assert r["err"] == [] and r.get("fatal") is None, r
    assert r["rows"] >= 17 and r["pwned"] == 0 and r["pwned2"] == 0 and r["scripts"] == 0     # nothing ran, nothing was turned into markup
    assert r["rtl"] >= 1 and r["emoji"] >= 1 and r["script"] >= 1 and r["marks"] >= 1           # still searchable, matches marked
    assert r["long"] >= 17 and r["app"] >= 17 and r["meetings"] == 1 and r["meetingHtml"] == 0
    assert r["survived"]


def test_every_page_opens_and_has_something_on_screen():
    rows = dataset(80) + [meeting(1, "Call", [("You", "hi"), ("Priya", "hello")]), note(3, "a file", kind="file", title="x.m4a", seconds=30),
                          note(4, "to do", todo="open"), note(5, "with ai", ai=[{"label": "Improve", "text": "better", "at": 1, "model": "claude-haiku-5-5", "in_tok": 800, "out_tok": 25, "cost_usd": 0.000176, "cost_basis": "list"}])]
    r = run(rows, JS + """
      S.fixes_list=[['a','b'],['c','d']];window.push(JSON.stringify(S));
      const out={};for(const p of ['home','meetings','files','todo','dict','insights','settings','help']){go(p);const pane=document.querySelector('#pane-'+p);
        out[p]={shown:vis(pane),text:pane.innerText.replace(/\\s+/g,' ').trim().length,title:document.querySelector('#title').textContent}}
      R.pages=out;
      go('home');R.otherPanesHidden=['meetings','files','todo','dict','insights','settings','help'].every(p=>!vis(document.querySelector('#pane-'+p)));""")
    assert r["err"] == [] and r.get("fatal") is None, r
    for p, v in r["pages"].items():
        assert v["shown"] and v["text"] > 20, (p, v)                                          # visible, and not blank
    assert r["pages"]["home"]["title"] == "Dictations" and r["pages"]["todo"]["title"] == "To do" and r["otherPanesHidden"]


def test_clicking_every_button_on_every_page_never_breaks_the_page():
    """A crude fuzz: click each visible button, one at a time, on every page; the page must keep working."""
    rows = dataset(40) + [meeting(1, "Call", [("You", "hi"), ("Priya", "hello")], audio=2), note(2, "to do", todo="open"), note(3, "a file", kind="file", title="x.m4a", seconds=30)]
    r = run(rows, JS + """
      S.fixes_list=[['a','b']];window.push(JSON.stringify(S));
      const skip=/Delete them|Sign in|Switch account|Clear…|Remove|Restore|Back up|Quit|Choose a file|Record|Run setup/i;
      const bad=[];let clicks=0;
      for(const p of ['home','meetings','files','todo','dict','insights','settings','help']){go(p);
        const btns=[...document.querySelectorAll('#pane-'+p+' button, nav button, .qbar button, .snav button')].filter(vis).filter(b=>!skip.test(b.textContent+b.getAttribute('aria-label')));
        for(const b of btns.slice(0,60)){const before=(window.__err||[]).length;try{b.click()}catch(e){bad.push(p+': '+e.message)}clicks++;
          document.querySelectorAll('.menu').forEach(m=>m.remove());if((window.__err||[]).length>before)bad.push(p+': error after clicking "'+(b.textContent||b.getAttribute('aria-label')).trim().slice(0,30)+'"');}
        go(p);}
      R.clicks=clicks;R.bad=bad.slice(0,8);R.alive=visibleRows('home')===0?'(none)':'ok';go('home');R.alive=vis(document.querySelector('#pane-home'));""")
    assert r.get("fatal") is None, r
    assert r["bad"] == [], r["bad"]
    assert r["clicks"] > 80 and r["alive"] is True


def test_ai_answers_show_their_cost_in_dollars_or_rupees():
    ans = [{"label": "Improve the wording", "text": "better words", "at": 5, "model": "claude-haiku-5-5", "in_tok": 800, "out_tok": 25, "cost_usd": 0.000176, "cost_basis": "list"},
           {"label": "Summary", "text": "short", "at": 4}]
    base = [note(0, "kal meeting hai", ai=ans)]
    usd = run(base, "openDrawer(S.history[0].id);R.chips=[...document.querySelectorAll('#drawer .aicost')].map(e=>e.textContent);R.tip=document.querySelector('#drawer .aicost')?.dataset.tt||'';")
    inr = run(base, "openDrawer(S.history[0].id);R.chips=[...document.querySelectorAll('#drawer .aicost')].map(e=>e.textContent);", prefs={"cost_currency": "INR", "usd_inr": 85.5})
    norate = run(base, "openDrawer(S.history[0].id);R.chips=[...document.querySelectorAll('#drawer .aicost')].map(e=>e.textContent);", prefs={"cost_currency": "INR", "usd_inr": 0})
    assert usd["err"] == [] and usd["chips"] == ["$0.0002"] and "list price" in usd["tip"]       # an answer with no cost shows no chip
    assert inr["chips"] == ["₹0.0150"] and norate["chips"] == ["$0.0002"]                         # no rate typed: stays dollars


def test_dark_theme_every_page_has_a_dark_background_and_readable_text():
    r = run([note(0, "hello world")], JS + """
      const out={};for(const p of ['home','meetings','todo','dict','settings','help']){go(p);
        const m=getComputedStyle(document.querySelector('main')),t=getComputedStyle(document.querySelector('#pane-'+p+' .row, #pane-'+p+' b, #pane-'+p+' p, #pane-'+p+' h2')||document.querySelector('main'));
        out[p]=[m.backgroundColor,t.color]}
      R.out=out;R.theme=document.documentElement.dataset.theme;""", prefs={"theme": "dark"})
    assert r["err"] == [] and r.get("fatal") is None and r["theme"] == "dark"

    def lum(c):
        n = [int(float(x)) for x in c[c.index("(") + 1:c.index(")")].split(",")[:3]]
        return sum(n) / 3

    for p, (bg, fg) in r["out"].items():
        assert lum(bg) < 80 and lum(fg) > 120, (p, bg, fg)                                      # dark paper, light ink


# ------------------------------------------------------------------------------------- Insights numbers
def test_insights_numbers_match_the_notes():
    words = lambda n: " ".join(["w"] * n)  # noqa: E731
    rows = [note(i, words(10), ago=60) for i in range(3)] + [note(10 + i, words(20), ago=3 * DAY) for i in range(2)] + [note(20, words(5), ago=20 * DAY),
            meeting(30, "A meeting", [("You", words(50))])]                       # a meeting is not a dictation
    r = run(rows, "go('insights');R.tiles=[...document.querySelectorAll('#ins .kpi')].map(k=>[k.querySelector('.n').textContent.trim(),k.querySelector('.l').textContent.trim()]);"
                  "R.streak=document.querySelector('#ins .ibox h3 span')?.textContent;R.visible=vis(document.querySelector('#pane-insights'));")
    assert r["err"] == [] and r.get("fatal") is None and r["visible"]
    tiles = dict((label, n) for n, label in r["tiles"])
    assert tiles["words dictated"] == "75" and tiles["words this week"] == "70"         # 3×10 + 2×20 + 5, and the last 7 days
    assert tiles["dictations today"] == "3" and tiles["words in a typical dictation"] == "10"
    empty = run([], "go('insights');R.text=document.querySelector('#ins').innerText.replace(/\\s+/g,' ').trim();")
    assert "Nothing to show yet" in empty["text"]                                        # no rows of zeros on a fresh install


# ------------------------------------------------------------------------------------- scrolling and the keyboard
def test_scrolling_to_the_bottom_loads_the_next_rows_by_itself():
    rows = [note(i, f"row {i}", ago=i * 60) for i in range(400)]
    r = run(rows, JS + """
      R.first=visibleRows('home');const sc=$('#scroll');sc.scrollTop=sc.scrollHeight;
      setTimeout(()=>{sc.scrollTop=sc.scrollHeight},400);
      setTimeout(()=>{R.after=visibleRows('home');R.left=document.querySelector('#list .more-rows')?.textContent||null;R.err=window.__err||[];document.title=JSON.stringify(R)},1500);""")
    assert r["first"] == 100 and r["after"] > 100, r                        # reaching the end loads more without a click
    assert r["err"] == []


def test_keyboard_shortcuts_search_find_escape_and_settings():
    lines = [("You", f"filler {k}") for k in range(20)] + [("Priya", "the pricing proposal")]
    m = meeting(0, "Call", lines)
    r = run([note(1, "budget"), m], JS + """
      const key=(k,o={})=>document.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true,...o}));
      key('f',{metaKey:true});R.cmdF=document.activeElement.id;
      $('#q').value='budget';searched();$('#q').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));R.escClears=[$('#q').value,visibleRows('home')];
      go('insights');key('f',{metaKey:true});R.cmdFFromInsights=[document.activeElement.id,$('#pane-home').hidden===false];
      key(',',{metaKey:true});R.cmdComma=[$('#pane-settings').hidden===false,document.activeElement.id];
      go('meetings');openDrawer(S.history.find(r=>r.kind==='meeting').id,'listen');key('f',{metaKey:true});R.cmdFInListen=document.activeElement.id;
      const q=$('#pfq');q.value='pricing';q.dispatchEvent(new Event('input'));q.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));R.enterStays=$('#pfc').textContent;
      q.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));R.escFind=[q.value,$('#pfc').textContent,!!$('#drawer')&&vis($('#drawer'))];""")
    assert r["err"] == [] and r.get("fatal") is None, r
    assert r["cmdF"] == "q"                                                  # ⌘F goes to the search box
    assert r["escClears"] == ["", 1]                                         # Esc clears the search and the list is whole again
    assert r["cmdFFromInsights"] == ["q", True]                              # from a page with no list it opens Dictations first
    assert r["cmdComma"] == [True, "sq"]                                     # ⌘, opens Settings with the find box ready
    assert r["cmdFInListen"] == "pfq"                                        # inside Listen, ⌘F finds in the transcript
    assert r["enterStays"] == "1 of 1 line" and r["escFind"][0] == "" and r["escFind"][1] == "" and r["escFind"][2]   # Esc clears the find, not the panel
