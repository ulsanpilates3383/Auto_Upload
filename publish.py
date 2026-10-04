# publish.py — 폴더 안의 사진·영상(1~10개)과 caption.txt를 인스타에 올립니다
# 영상 1개만 있으면 릴스로, 여러 개면 사진·영상을 섞은 슬라이드로 올려요
import os, sys, glob, time, urllib.parse, requests

API = "https://graph.instagram.com/v21.0"
USER = os.environ["IG_USER_ID"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]
BASE = os.environ["IMG_BASE"].rstrip("/")
folder = sys.argv[1].strip("/")
PHOTO, VIDEO = (".jpg", ".jpeg"), (".mp4", ".mov")


def call(path, **data):
    data["access_token"] = TOKEN
    r = requests.post(f"{API}/{path}", data=data, timeout=60).json()
    if "error" in r:
        e = r["error"]
        sys.exit(f"오류(#{e.get('code')}): {e.get('message')}")
    return r["id"]


def wait(box, what):
    """인스타가 사진·영상을 다 받아 갈 때까지 기다립니다 (영상은 몇 분 걸릴 수 있어요)"""
    for _ in range(100):
        state = requests.get(f"{API}/{box}", params={"fields": "status_code,status", "access_token": TOKEN}, timeout=30).json()
        code = state.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            sys.exit(f"오류(처리 실패): 인스타가 {what}을(를) 받지 못했어요 — {state.get('status', '')}")
        time.sleep(6)
    sys.exit(f"오류(처리 시간 초과): {what} 처리가 10분 넘게 끝나지 않았어요")


if os.path.exists(f"{folder}/posted.txt"):
    sys.exit(f"{folder}는 이미 올린 폴더예요. 다시 올리려면 posted.txt를 지우세요")

items = sorted(p for p in glob.glob(f"{folder}/*") if p.lower().endswith(PHOTO + VIDEO))[:10]
if not items:
    sys.exit(f"오류: {folder} 폴더에 JPG 사진이나 MP4·MOV 영상이 없어요")
cap_file = f"{folder}/caption.txt"
caption = open(cap_file, encoding="utf-8").read() if os.path.exists(cap_file) else ""


def url(p):
    return BASE + "/" + urllib.parse.quote(p.replace("\\", "/"))


def is_video(p):
    return p.lower().endswith(VIDEO)


if len(items) == 1:
    p = items[0]
    if is_video(p):
        box = call(f"{USER}/media", media_type="REELS", video_url=url(p), caption=caption, share_to_feed="true")
    else:
        box = call(f"{USER}/media", image_url=url(p), caption=caption)
else:
    kids = []
    for p in items:
        if is_video(p):
            kid = call(f"{USER}/media", media_type="VIDEO", video_url=url(p), is_carousel_item="true")
        else:
            kid = call(f"{USER}/media", image_url=url(p), is_carousel_item="true")
        wait(kid, os.path.basename(p))
        kids.append(kid)
    box = call(f"{USER}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)

wait(box, "게시물")
post_id = call(f"{USER}/media_publish", creation_id=box)
open(f"{folder}/posted.txt", "w").write(post_id)  # 두 번 올라가지 않게 표시
print("게시 완료! 게시물 번호:", post_id)
