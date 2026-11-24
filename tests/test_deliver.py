"""Buttondown delivery, with a fake HTTP session (no network)."""
from radar import config, deliver


class Resp:
    def __init__(self, data, code=200):
        self._d, self.status_code, self.text = data, code, str(data)

    def json(self):
        return self._d


class FakeButtondown:
    def __init__(self, tags, subs=None, merge_on_patch=False):
        self.tags, self.subs, self.merge = tags, subs or {}, merge_on_patch
        self.posts, self.headers = [], []

    def get(self, url, params=None, timeout=None, headers=None):
        self.headers.append(headers)
        if url.endswith("/tags"):
            return Resp({"results": [{"name": n, "id": i} for n, i in self.tags.items()], "next": None})
        tag = (params or {}).get("tag")
        return Resp({"results": [{"id": k, "tags": list(v)} for k, v in self.subs.items() if tag in v], "next": None})

    def post(self, url, json=None, timeout=None, headers=None):
        self.posts.append(json); self.headers.append(headers)
        return Resp({"id": f"em_{len(self.posts)}", "status": json["status"]})

    def patch(self, url, json=None, timeout=None, headers=None):
        sid = url.rsplit("/", 1)[1]
        self.subs[sid] = sorted(set(self.subs[sid]) | set(json["tags"])) if self.merge else json["tags"]
        return Resp({"id": sid, "tags": self.subs[sid]})


ISSUE = "# Council Radar: Ontario Energy Projects\n*Week of November 23, 2026*\n\n**1 items from 1 municipalities this week.**\n"


def test_issue_subject_and_audiences(tmp_path):
    p = tmp_path / "2026-11-23-energy.md"; p.write_text(ISSUE)
    subject, body = deliver.issue_from_markdown(p)
    assert subject == "Council Radar: Ontario Energy Projects | week of November 23, 2026"
    plan = deliver.plan_weekly(subject, body)
    assert [x["tag"] for x in plan] == ["active", "trial-1", "trial-2"]
    for x in plan:  # CASL footer on every audience
        assert "230 Regina Street North, Waterloo, ON" in x["body"] and "Reply 'unsubscribe'" in x["body"]
    assert "trial issue 1 of 2" in plan[1]["body"] and "trial issue 2 of 2" in plan[2]["body"]
    assert "trial issue" not in plan[0]["body"]


def test_send_weekly_filters_by_tag_id_and_skips_missing_tags(monkeypatch):
    monkeypatch.setattr(config, "BUTTONDOWN_API_KEY", "k")
    fake = FakeButtondown({"active": "tag_a", "trial-1": "tag_t1"})
    res = deliver.send_weekly("S", ISSUE, mode="draft", session=fake)
    assert [r.get("skipped") for r in res] == [None, None, "tag does not exist yet"]
    assert [p["filters"]["filters"][0]["value"] for p in fake.posts] == ["tag_a", "tag_t1"]
    assert all(p["status"] == "draft" for p in fake.posts)
    assert all("X-Buttondown-Live-Dangerously" not in h for h in fake.headers)  # drafts need no confirmation
    assert all(h["Authorization"] == "Token k" and h["X-API-Version"] == deliver.API_VERSION for h in fake.headers)


def test_real_send_sets_live_header(monkeypatch):
    monkeypatch.setattr(config, "BUTTONDOWN_API_KEY", "k")
    fake = FakeButtondown({"active": "tag_a"})
    deliver.send_weekly("S", ISSUE, mode="send", session=fake)
    assert fake.posts[0]["status"] == "about_to_send"
    assert fake.headers[-1]["X-Buttondown-Live-Dangerously"] == "true"


def test_advance_trials_moves_each_reader_one_step(monkeypatch):
    monkeypatch.setattr(config, "BUTTONDOWN_API_KEY", "k")
    fake = FakeButtondown({}, {"s1": ["trial-1"], "s2": ["trial-2", "law"], "s3": ["active"]})
    deliver.advance_trials(session=fake)
    assert fake.subs == {"s1": ["trial-2"], "s2": ["law", "trial-ended"], "s3": ["active"]}


def test_advance_trials_stops_if_patch_merges(monkeypatch):
    import pytest
    monkeypatch.setattr(config, "BUTTONDOWN_API_KEY", "k")
    fake = FakeButtondown({}, {"s1": ["trial-1"]}, merge_on_patch=True)
    with pytest.raises(RuntimeError, match="merged"):
        deliver.advance_trials(session=fake)


def test_no_key_means_no_call(monkeypatch):
    import pytest
    monkeypatch.setattr(config, "BUTTONDOWN_API_KEY", "")
    with pytest.raises(RuntimeError, match="not set"):
        deliver.send_weekly("S", ISSUE, session=FakeButtondown({}))
