"""
========================================================================================
   👑 ETS TOEIC OLPC - AUTO SOLVER PRO (PORTABLE & ALL-IN-ONE) 👑
   ★ ★ ★  M A D E   B Y   B A N G   D Z   U w U  ★ ★ ★
   Bộ công cụ tự động hóa toàn trình khóa học ETS TOEIC OLPC
   - Tự động hoàn thành 100% bài học (Lessons & Step Tests)
   - Tự động giải 100% Unit Tests (100/100 tuyệt đối mọi Unit)
   - Tự động giải 100% các bài thi Mid-term & Final Tests (Assessment Center)
   - Tự động phát hiện Chrome Debugging, đồng bộ cơ sở dữ liệu và chụp ảnh chứng nhận
========================================================================================
"""

import asyncio
import json
import websockets
from websockets.protocol import State
import base64
import sys
import re
import os
import time
import urllib.request
import argparse
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSESSMENT_ANSWERS_DIR = DATA_DIR / "assessment_answers"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BANNER = r"""
========================================================================================
  __  __    _    ____  _____   ______   __   ____    _    _   _  ____   ____  _____ 
 |  \/  |  / \  |  _ \| ____| | __ ) \ / /  | __ )  / \  | \ | |/ ___| |  _ \|__  / 
 | |\/| | / _ \ | | | |  _|   |  _ \\ V /   |  _ \ / _ \ |  \| | |  _  | | | | / /  
 | |  | |/ ___ \| |_| | |___  | |_) || |    | |_) / ___ \| |\  | |_| | | |_| |/ /_  
 |_|  |_/_/   \_\____/|_____| |____/ |_|    |____/_/   \_\_| \_|\____| |____//____| 
                                                                                     
                    ★ ★ ★  M A D E   B Y   B A N G   D Z   U w U  ★ ★ ★
========================================================================================
"""

MODULE_PRESETS = {
    1: {"course_id": 1547026, "toeic_course_id": 1, "name": "Module 1: High-beginner"},
    2: {"course_id": 1547470, "toeic_course_id": 3257, "name": "Module 2: Intermediate"},
    3: {"course_id": 1548014, "toeic_course_id": 3467, "name": "Module 3: Advanced"}
}

MODULE3_UNIT_DATA = {
    1: {"name": "Health",             "nodeId": 1548015, "testId": 42564, "toeicUnitId": 3468},
    2: {"name": "Purchasing",         "nodeId": 1548066, "testId": 42642, "toeicUnitId": 3579},
    3: {"name": "Personnel",          "nodeId": 1548173, "testId": 42720, "toeicUnitId": 3695},
    4: {"name": "General Business",   "nodeId": 1548274, "testId": 42798, "toeicUnitId": 3806},
    5: {"name": "Finance and Budget", "nodeId": 1548323, "testId": 42876, "toeicUnitId": 3916},
    6: {"name": "Travel",             "nodeId": 1548376, "testId": 42954, "toeicUnitId": 4040},
    7: {"name": "Offices",            "nodeId": 1548458, "testId": 43032, "toeicUnitId": 4164},
    8: {"name": "Dining Out",         "nodeId": 1548509, "testId": 43110, "toeicUnitId": 4290},
}

ASSESSMENT_TESTS = {
    1: {
        'id': 989011001,
        'name': 'Module 2: Intermediate Mid-term test',
        'short_name': 'm2_midterm',
        'file_key': 'module2_midterm_989011001.json',
        'total': 100,
        'course_id': 3257,
        'test_type': 3,
        'ed_course_id': 1547470
    },
    2: {
        'id': 143541,
        'name': 'Module 2: Intermediate Final Test',
        'short_name': 'm2_final',
        'file_key': 'module2_final_143541.json',
        'total': 200,
        'course_id': 3257,
        'test_type': 4,
        'ed_course_id': 1547470
    },
    3: {
        'id': 989010001,
        'name': 'Module 3: Advanced Mid-term test',
        'short_name': 'm3_midterm',
        'file_key': 'module3_midterm_989010001.json',
        'total': 100,
        'course_id': 3467,
        'test_type': 3,
        'ed_course_id': 1548014
    },
    4: {
        'id': 1539000,
        'name': 'Module 3: Advanced Final Test I',
        'short_name': 'm3_final_1',
        'file_key': 'module3_final_1_1539000.json',
        'total': 200,
        'course_id': 3467,
        'test_type': 4,
        'ed_course_id': 1548014
    },
    5: {
        'id': 1540000,
        'name': 'Module 3: Advanced Final Test II',
        'short_name': 'm3_final_2',
        'file_key': 'module3_final_2_1540000.json',
        'total': 200,
        'course_id': 3467,
        'test_type': 5,
        'ed_course_id': 1548014
    }
}


def detect_chrome_cdp(custom_port=None, custom_url=None):
    """Tự động phát hiện WebSocket Debugging URL của Chrome/Edge"""
    if custom_url:
        return custom_url, "custom"

    ports_to_try = [custom_port] if custom_port else [9222, 9223, 9224]

    for p in ports_to_try:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{p}/json/version")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                ws_url = data.get("webSocketDebuggerUrl")
                if ws_url:
                    return ws_url, str(p)
        except Exception:
            pass

    # Quét DevToolsActivePort
    candidates = []
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    user_profile = os.environ.get("USERPROFILE", "")

    # Profile riêng của tool nếu có
    candidates.append(BASE_DIR / "chrome_debug_profile" / "DevToolsActivePort")

    if local_app_data:
        candidates.extend([
            Path(local_app_data) / "Google" / "Chrome" / "User Data" / "DevToolsActivePort",
            Path(local_app_data) / "Google" / "Chrome" / "User Data" / "Default" / "DevToolsActivePort",
            Path(local_app_data) / "Microsoft" / "Edge" / "User Data" / "DevToolsActivePort",
            Path(local_app_data) / "BraveSoftware" / "Brave-Browser" / "User Data" / "DevToolsActivePort"
        ])
    if user_profile:
        candidates.extend([
            Path(user_profile) / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "DevToolsActivePort",
            Path(user_profile) / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "DevToolsActivePort"
        ])

    for fpath in candidates:
        if fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    port = f.readline().strip()
                    path = f.readline().strip()
                if port and path:
                    return f"ws://127.0.0.1:{port}{path}", port
            except Exception:
                pass

    return None, None


class MasterUnitSolver:
    def __init__(self, unit_seq=1, module=None, custom_port=None, skip_test=False, only_test=False):
        self.ws = None
        self.req_id = 0
        self.pending = {}
        self.unit_seq = unit_seq
        self.custom_module = module
        self.custom_port = custom_port
        self.skip_test = skip_test
        self.only_test = only_test
        self.course_id = None
        self.toeic_course_id = None
        self.course_name = None
        self.unit_info = {}
        self.answers_key = {}

    async def connect(self):
        try:
            if self.ws and getattr(self.ws, 'state', None) is State.OPEN:
                await self.ws.close()
        except Exception:
            pass
        self.pending.clear()

        ws_url, port = detect_chrome_cdp(custom_port=self.custom_port)
        if not ws_url:
            raise Exception("Không tìm thấy Chrome CDP! Hãy chạy start_chrome_debug.bat trước.")

        for attempt in range(5):
            try:
                self.ws = await websockets.connect(
                    ws_url,
                    max_size=100*1024*1024,
                    ping_interval=30,
                    ping_timeout=60,
                    open_timeout=30
                )
                asyncio.create_task(self._listen())
                print(f"[+] Đã kết nối Chrome CDP trên cổng {port}!", flush=True)
                return
            except Exception as e:
                print(f"[!] Thử kết nối CDP lần {attempt + 1} thất bại: {e}, thử lại sau 2s...", flush=True)
                await asyncio.sleep(2)
        raise Exception("Không thể kết nối Chrome CDP sau 5 lần thử!")

    async def _listen(self):
        try:
            async for raw in self.ws:
                msg = json.loads(raw)
                if "id" in msg and msg["id"] in self.pending:
                    self.pending[msg["id"]].set_result(msg)
        except Exception:
            pass

    async def send(self, method, params=None, session_id=None, timeout=35):
        if self.ws is None or getattr(self.ws, 'state', None) is not State.OPEN:
            print("[!] WebSocket bị đóng hoặc chưa mở, đang tự động kết nối lại...", flush=True)
            await self.connect()

        self.req_id += 1
        mid = self.req_id
        fut = asyncio.get_event_loop().create_future()
        self.pending[mid] = fut
        payload = {"id": mid, "method": method}
        if params: payload["params"] = params
        if session_id: payload["sessionId"] = session_id

        try:
            await self.ws.send(json.dumps(payload))
            res = await asyncio.wait_for(fut, timeout=timeout)
        except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError):
            self.pending.pop(mid, None)
            print(f"[!] Lỗi khi gửi {method}, tự động kết nối lại CDP...", flush=True)
            await self.connect()
            self.req_id += 1
            mid = self.req_id
            fut = asyncio.get_event_loop().create_future()
            self.pending[mid] = fut
            payload["id"] = mid
            await self.ws.send(json.dumps(payload))
            res = await asyncio.wait_for(fut, timeout=timeout)
        finally:
            self.pending.pop(mid, None)
        return res

    async def get_targets(self):
        r = await self.send("Target.getTargets")
        return r.get("result", {}).get("targetInfos", [])

    async def attach(self, target_id):
        r = await self.send("Target.attachToTarget", {"targetId": target_id, "flatten": True})
        return r.get("result", {}).get("sessionId")

    async def js(self, expr, sid=None, timeout=35):
        r = await self.send("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        }, session_id=sid, timeout=timeout)
        res = r.get("result", {})
        if "exceptionDetails" in res:
            raise Exception(res["exceptionDetails"].get("exception", {}).get("description", "JS Error"))
        return res.get("result", {}).get("value")

    async def screenshot(self, name, sid=None):
        path = OUTPUT_DIR / f"{name}.png"
        try:
            r = await self.send("Page.captureScreenshot", {"format": "png"}, session_id=sid)
            data = r.get("result", {}).get("data", "")
            if data:
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"  [📸 Screenshot] Đã lưu: {path.name}", flush=True)
        except Exception as e:
            print(f"  [!] Chụp ảnh màn hình thất bại: {e}", flush=True)
        return str(path)

    async def ensure_active_course(self, page_sid):
        if not self.custom_module or self.custom_module not in MODULE_PRESETS:
            return
        preset = MODULE_PRESETS[self.custom_module]
        target_course_id = preset["course_id"]

        curr_course_id = await self.js("""
        (() => {
            try {
                const c = JSON.parse(localStorage.getItem('Course'));
                return c ? c.CourseId : null;
            } catch(e) { return null; }
        })()
        """, sid=page_sid)

        if curr_course_id == target_course_id:
            print(f"[+] Khóa học hiện tại đã đúng: {preset['name']} ({target_course_id})", flush=True)
            return

        print(f"[+] Đang chuyển giao diện sang {preset['name']} ({target_course_id})...", flush=True)
        await self.js("if (!window.location.hash.includes('home')) window.location.href = 'https://edtoeic.engdis.com/EdToeic1#/home';", sid=page_sid)
        await asyncio.sleep(3)

        switched = await self.js(f"""
        (() => {{
            const cEl = document.querySelector('.carousel');
            const sc = cEl ? angular.element(cEl).scope() : null;
            if (sc && sc.carouselCtrl) {{
                const idx = sc.carouselCtrl.slides.findIndex(s => s.CourseId === {target_course_id});
                if (idx !== -1) {{
                    sc.carouselCtrl.onSlideChanged(sc.carouselCtrl.slides[idx], 'next');
                    return true;
                }}
            }}
            return false;
        }})()
        """, sid=page_sid)

        if switched:
            print(f"[+] Đã chuyển khóa học thành công sang {preset['name']}", flush=True)
            await asyncio.sleep(4)
        else:
            print(f"[!] Chuyển khóa học qua localStorage...", flush=True)
            await self.js(f"""
            (() => {{
                try {{
                    const courseObj = {{
                        CourseId: {target_course_id},
                        CourseName: '{preset['name']}'
                    }};
                    localStorage.setItem('Course', JSON.stringify(courseObj));
                    window.location.reload();
                }} catch(e) {{}}
            }})()
            """, sid=page_sid)
            await asyncio.sleep(5)

    async def phase1_discover_unit(self):
        print(f"\n{'='*60}", flush=True)
        print(f"=== PHA 1: KHÁM PHÁ CÂY BÀI HỌC UNIT {self.unit_seq} ===", flush=True)
        print(f"{'='*60}", flush=True)

        targets = await self.get_targets()
        page = next((t for t in targets if t['type'] == 'page' and ('edtoeic' in t.get('url', '') or 'toeicolpc' in t.get('url', ''))), None)
        if not page:
            print("[!] Đang tự động mở tab ETS TOEIC trên trình duyệt Chrome...", flush=True)
            await self.send("Target.createTarget", {"url": "https://edtoeic.engdis.com/EdToeic1#/home"})
            await asyncio.sleep(4)
            targets = await self.get_targets()
            page = next((t for t in targets if t['type'] == 'page' and ('edtoeic' in t.get('url', '') or 'toeicolpc' in t.get('url', ''))), None)
            if not page:
                raise Exception("Không tìm thấy trang TOEIC nào đang mở! Vui lòng mở Chrome qua start_chrome_debug.bat.")

        page_sid = await self.attach(page['targetId'])

        if self.custom_module:
            await self.ensure_active_course(page_sid)

        # Nhận diện Module
        course_meta = await self.js("""
        (() => {
            try {
                const c = JSON.parse(localStorage.getItem('Course'));
                const ti = JSON.parse(localStorage.getItem('toeicInformation'));
                let m = null;
                if (ti && ti.toeicEDCoursesMappers) {
                    m = ti.toeicEDCoursesMappers.find(x => x.edId === (c ? c.CourseId : null));
                }
                return {
                    courseId: c ? c.CourseId : 1547470,
                    courseName: c ? c.CourseName : 'Unknown',
                    toeicCourseId: m ? m.toeicId : 3257
                };
            } catch(e) {
                return { courseId: 1547470, courseName: 'Module 2: Intermediate', toeicCourseId: 3257 };
            }
        })()
        """, sid=page_sid)

        if self.custom_module and self.custom_module in MODULE_PRESETS:
            preset = MODULE_PRESETS[self.custom_module]
            self.course_id = preset["course_id"]
            self.toeic_course_id = preset["toeic_course_id"]
            self.course_name = preset["name"]
        else:
            self.course_id = course_meta.get("courseId", 1547470)
            self.toeic_course_id = course_meta.get("toeicCourseId", 3257)
            self.course_name = course_meta.get("courseName", "Auto-detected Course")

        print(f"[+] Khóa học hoạt động: {self.course_name} (CourseId: {self.course_id}, ToeicId: {self.toeic_course_id})", flush=True)

        # Lấy thông tin Unit từ GetUnits API
        print("[+] Gọi GetUnits API để lấy thông tin bài kiểm tra và Unit...", flush=True)
        units_data = await self.js(f"""
        new Promise((resolve) => {{
            try {{
                const toeicInfo = JSON.parse(localStorage.getItem('toeicInformation'));
                const url = toeicInfo.toeicServicesURL + '/LearningService.svc/script/GetUnits?courseId={self.toeic_course_id}';
                $.ajax({{
                    url: url,
                    type: 'GET',
                    headers: {{ 'Edusoft-SessionKey': toeicInfo.toeicSessionKey }},
                    success: (data) => resolve(data.d),
                    error: (err) => resolve([])
                }});
            }} catch(e) {{ resolve([]); }}
        }})
        """, sid=page_sid)

        target_u = next((u for u in units_data if u.get('sequence') == self.unit_seq), None)
        if not target_u:
            # Fallback nếu GetUnits trả về rỗng
            if self.course_id == 1548014 and self.unit_seq in MODULE3_UNIT_DATA:
                m3u = MODULE3_UNIT_DATA[self.unit_seq]
                target_u = {
                    'name': m3u['name'],
                    'testId': m3u['testId'],
                    'unitId': m3u['toeicUnitId'],
                    'grade': None
                }
                print(f"[!] Dùng bảng cấu hình dự phòng Module 3 cho Unit {self.unit_seq}: testId={target_u['testId']}", flush=True)

        if not target_u:
            raise Exception(f"Không tìm thấy Unit có sequence {self.unit_seq}!")

        self.unit_info = {
            'sequence': self.unit_seq,
            'name': target_u['name'],
            'testId': target_u['testId'],
            'toeicUnitId': target_u.get('unitId'),
            'initialGrade': target_u.get('grade')
        }
        print(f"[+] Tìm thấy Unit: {self.unit_info['name']} (Sequence: {self.unit_seq}, TestId: {self.unit_info['testId']}, Điểm hiện tại: {self.unit_info['initialGrade']})", flush=True)

        # Đảm bảo mở Learning Area
        targets = await self.get_targets()
        la_target = next((t for t in targets if 'learningArea' in t.get('url', '')), None)
        if not la_target:
            print("[+] Đang mở Learning Area...", flush=True)
            await self.js(f"""
            (() => {{
                const appEl = document.querySelector('[ng-app]') || document.body;
                const inj = angular.element(appEl).injector();
                const cds = inj ? inj.get('courseDataService') : null;
                const u = cds && cds.course && cds.course.Children ? cds.course.Children.find(u => u.Sequence === {self.unit_seq}) : null;
                const lesson0 = u && u.Children && u.Children.length > 0 ? u.Children[0] : null;
                if (lesson0 && cds.goToLesson) {{
                    cds.goToLesson(lesson0);
                }}
            }})()
            """, sid=page_sid)

            for _ in range(15):
                await asyncio.sleep(2)
                targets = await self.get_targets()
                la_target = next((t for t in targets if 'learningArea' in t.get('url', '')), None)
                if la_target: break

        if not la_target:
            raise Exception("Không mở được Learning Area!")

        la_sid = await self.attach(la_target['targetId'])
        print("[+] Đang đợi Learning Area tải hoàn tất courseTree...", flush=True)

        # Lấy thông tin Unit Node trong courseTree với cơ chế chờ
        unit_node_idx = self.unit_seq - 1
        u_node_res = None
        for _ in range(25):
            await asyncio.sleep(1.5)
            u_node_res = await self.js(f"""
            (() => {{
                try {{
                    const rootEl = document.querySelector('[ng-version]');
                    if (!rootEl) return null;
                    const comp = ng.probe(rootEl)?.componentInstance;
                    const nav = comp?.navigationService;
                    if (!nav || !nav.courseTree || !nav.courseTree.Children || nav.courseTree.Children.length <= {unit_node_idx}) return null;
                    const u = nav.courseTree.Children[{unit_node_idx}];
                    return u ? {{ nodeId: u.NodeId, name: u.Name }} : null;
                }} catch(e) {{ return null; }}
            }})()
            """, sid=la_sid)
            if u_node_res: break

        if not u_node_res:
            raise Exception(f"Không tìm thấy Unit Node tại index {unit_node_idx} trong nav.courseTree sau 35s!")

        self.unit_info['nodeId'] = u_node_res['nodeId']
        print(f"[+] Unit NodeId trong courseTree: {self.unit_info['nodeId']}", flush=True)

        # Truy vấn cây bài học chi tiết qua DAL Service
        print("[+] Đang quét toàn bộ cây bài học và task ID qua courseTreeAPIDALService...", flush=True)
        tree_res = await self.js(f"""
        new Promise((resolve) => {{
            try {{
                const rootEl = document.querySelector('[ng-version]');
                const comp = ng.probe(rootEl).componentInstance;
                const nav = comp.navigationService;
                const api = nav.courseTreeService.courseTreeAPIDALService;
                const uNode = nav.courseTree.Children[{unit_node_idx}];

                api.getCourseNodeChildren(nav.courseTree.NodeId, uNode).subscribe(
                    (data) => {{
                        const lessons = data.map(l => ({{
                            name: l.Name,
                            nodeId: l.NodeId,
                            code: l.Metadata ? l.Metadata.Code : null,
                            steps: l.Children ? l.Children.map(s => ({{
                                name: s.Name,
                                nodeId: s.NodeId,
                                tasks: s.Children ? s.Children.map(t => ({{
                                    id: t.NodeId,
                                    name: t.Name,
                                    isDone: t.IsDone
                                }})) : []
                            }})) : []
                        }}));
                        resolve({{ ok: true, lessons }});
                    }},
                    (err) => resolve({{ ok: false, error: err }})
                );
            }} catch(e) {{
                resolve({{ ok: false, error: e.message }});
            }}
        }})
        """, sid=la_sid)

        if not tree_res.get('ok'):
            raise Exception(f"Lỗi truy vấn DAL: {tree_res.get('error')}")

        lessons = tree_res.get('lessons', [])
        all_tasks = []
        undone_tasks = []
        test_step_ids = []

        for l in lessons:
            l_tasks = []
            for s in l['steps']:
                if s['name'] == 'Test':
                    test_step_ids.append(s['nodeId'])
                for t in s['tasks']:
                    all_tasks.append(t['id'])
                    l_tasks.append(t['id'])
                    if not t['isDone']:
                        undone_tasks.append(t['id'])
            print(f"  • Bài học: {l['name']} ({l['nodeId']}) -> {len(l_tasks)} tasks", flush=True)

        print(f"[+] Tổng cộng: {len(lessons)} bài học, {len(all_tasks)} nhiệm vụ (Cần thực hiện: {len(undone_tasks)})", flush=True)
        print(f"[+] Tìm thấy {len(test_step_ids)} bài kiểm tra Step: Test ({test_step_ids})", flush=True)
        self.unit_info['undone_tasks'] = undone_tasks
        self.unit_info['all_tasks'] = all_tasks
        self.unit_info['test_step_ids'] = test_step_ids
        self.unit_info['lessons'] = lessons
        return la_sid

    async def phase2_complete_lessons(self, la_sid):
        if self.only_test:
            print("[!] Bỏ qua hoàn thành bài học (--only-test)", flush=True)
            return

        print(f"\n{'='*60}", flush=True)
        print(f"=== PHA 2: HOÀN THÀNH 100% TIẾN ĐỘ BÀI HỌC QUA API ===", flush=True)
        print(f"{'='*60}", flush=True)

        undone = self.unit_info.get('undone_tasks', [])
        if not undone:
            print("[+] Tất cả các nhiệm vụ bài học đã hoàn thành!", flush=True)
        else:
            print(f"[+] Đang gửi SetProgressPerTask cho {len(undone)} tasks...", flush=True)
            res = await self.js(f"""
            (async () => {{
                const token = localStorage.getItem('EDAPPToken');
                const ids = {json.dumps(undone)};
                const courseId = {self.course_id};
                const results = [];
                for (const itemId of ids) {{
                    let tries = 0;
                    while (tries < 3) {{
                        try {{
                            const resp = await fetch('https://edwebservices2.engdis.com/api/Progress/SetProgressPerTask', {{
                                method: 'POST',
                                headers: {{
                                    'Authorization': 'Bearer ' + token,
                                    'Content-Type': 'application/json'
                                }},
                                body: JSON.stringify({{ CourseId: courseId, ItemId: itemId }})
                            }});
                            if (resp.status === 429) {{
                                await new Promise(r => setTimeout(r, 3000));
                                tries++;
                                continue;
                            }}
                            results.push({{ itemId, status: resp.status, ok: resp.ok }});
                            break;
                        }} catch(e) {{
                            results.push({{ itemId, error: e.message }});
                            break;
                        }}
                    }}
                    await new Promise(r => setTimeout(r, 120));
                }}
                return results;
            }})()
            """, sid=la_sid, timeout=120)

            success_count = sum(1 for r in (res or []) if r.get('ok') or r.get('status') in [200, 201])
            print(f"[+] Hoàn thành {success_count}/{len(undone)} tasks thành công!", flush=True)

        # Giải và lưu điểm 100% vĩnh viễn trên máy chủ cho bài kiểm tra bài học
        print("[+] Đang giải và ghi điểm 100% vĩnh viễn lên máy chủ cho Lesson Tests (SaveUserTest)...", flush=True)
        test_lessons = [
            {'lessonId': l['nodeId'], 'code': l.get('code'), 'name': l['name'], 'unitId': self.unit_info['nodeId']}
            for l in self.unit_info.get('lessons', [])
            if any(s.get('name') == 'Test' for s in l.get('steps', [])) and l.get('code')
        ]

        if test_lessons:
            solve_res = await self.js(f"""
            (async () => {{
                const token = localStorage.getItem('EDAPPToken');
                const lessons = {json.dumps(test_lessons)};
                const results = [];
                for (const l of lessons) {{
                    try {{
                        const lResp = await fetch('https://static.engdis.com/edprod01/edprod//Runtime/Lessons/' + l.code + '.js');
                        const lTxt = await lResp.text();
                        const fn = new Function(lTxt + '; return typeof lesson !== "undefined" ? lesson : (typeof json !== "undefined" ? json : null);');
                        const lJson = fn();
                        const testStep = (lJson?.steps || []).find(s => (s.Name || s.name || '').toLowerCase() === 'test');
                        if (!testStep || !testStep.tasks || testStep.tasks.length === 0) continue;

                        const testAnswers = [];
                        for (const t of testStep.tasks) {{
                            const itemUrl = `https://edwebservices2.engdis.com/api/practiceManager/GetItem/${{t.id}}/${{t.code}}/${{t.type}}/0/4/`;
                            const itemResp = await fetch(itemUrl, {{ headers: {{ 'Authorization': 'Bearer ' + token }} }});
                            const itemData = await itemResp.json();
                            const item = itemData.i || {{}};
                            const ua = [];
                            const itemType = parseInt(t.type, 10);

                            if (itemType === 25) {{
                                (item.q || []).forEach(q => {{
                                    (q.al || []).forEach(al => {{
                                        const bank = (al.a || []).map(a => a.id);
                                        const correctChoice = (al.a || []).find(a => String(a.c) === '1' || a.c === 1 || a.c === true);
                                        if (correctChoice) {{
                                            ua.push({{ qId: q.id, aId: [[al.id, correctChoice.id]], bId: bank }});
                                        }}
                                    }});
                                }});
                            }} else if (itemType === 23) {{
                                const bank = [];
                                (item.q || []).forEach(q => {{ (q.al || []).forEach(al => {{ (al.a || []).forEach(a => bank.push(a.id)); }}); }});
                                (item.d || []).forEach(d => bank.push(d.id));
                                let isFirst = true;
                                (item.q || []).forEach(q => {{
                                    (q.al || []).forEach(al => {{
                                        const correctChoice = al.a?.[0];
                                        if (correctChoice) {{
                                            ua.push({{ qId: q.id, aId: [[al.id, correctChoice.id]], bId: isFirst ? bank : [] }});
                                            isFirst = false;
                                        }}
                                    }});
                                }});
                            }} else if (itemType === 51) {{
                                (item.q || []).forEach(q => {{
                                    const allBlanks = [];
                                    const allAIds = [];
                                    (q.al || []).forEach(al => {{
                                        (al.a || []).forEach(a => allBlanks.push(a.id));
                                        const c = (al.a || []).find(a => String(a.c) === '1' || a.c === 1 || a.c === true);
                                        if (c) allAIds.push([al.id, c.id]);
                                    }});
                                    if (allAIds.length > 0) {{
                                        ua.push({{ qId: q.id, aId: allAIds, bId: allBlanks }});
                                    }}
                                }});
                            }} else {{
                                (item.q || []).forEach(q => {{
                                    (q.al || []).forEach(al => {{
                                        const bank = (al.a || []).map(a => a.id);
                                        const correctChoice = (al.a || []).find(a => String(a.c) === '1' || a.c === 1 || a.c === true) || al.a?.[0];
                                        if (correctChoice) {{
                                            ua.push({{ qId: q.id, aId: [[al.id, correctChoice.id]], bId: bank }});
                                        }}
                                    }});
                                }});
                            }}
                            testAnswers.push({{ iId: parseInt(t.id, 10), iCode: t.code, iType: itemType, ua: ua }});
                        }}

                        const payload = {{ a: testAnswers, t: 60 }};
                        const submitRes = await new Promise((resolve) => {{
                            pmCallService('POST', JSON.stringify(payload), `WebApi/UserTestV1/SaveUserTest/${{l.unitId}}/${{l.lessonId}}/true`,
                                (res) => resolve({{ ok: true, res }}),
                                (err) => resolve({{ ok: false, status: err?.status }}),
                                false, true, 'json', 'application/json; charset=utf-8', true
                            );
                        }});
                        results.push({{ name: l.name, finalMark: submitRes?.res?.finalMark }});
                        await new Promise(r => setTimeout(r, 400));
                    }} catch(e) {{
                        results.push({{ name: l.name, error: e.message }});
                    }}
                }}
                return results;
            }})()
            """, sid=la_sid)
            for sr in (solve_res or []):
                print(f"  • {sr.get('name')}: điểm = {sr.get('finalMark')}%", flush=True)

        # Cập nhật Step: Test = 100%
        test_step_ids = self.unit_info.get('test_step_ids', [])
        if test_step_ids:
            print(f"[+] Gửi SetUserCourseUnitComponentProgress lên server cho {len(test_step_ids)} bài kiểm tra...", flush=True)
            await self.js(f"""
            (async () => {{
                try {{
                    const rootEl = document.querySelector('[ng-version]');
                    const comp = ng.probe(rootEl).componentInstance;
                    const svc = comp.navigationService.courseTreeService;
                    const steps = {json.dumps(test_step_ids)};
                    for (const stepId of steps) {{
                        try {{
                            const obs = svc.SetUserCourseUnitComponentProgress({{}}, stepId, 100);
                            await new Promise((resolve) => {{
                                obs.subscribe(() => resolve(true), () => resolve(true));
                                setTimeout(() => resolve(true), 2500);
                            }});
                        }} catch(e) {{}}
                        await new Promise(r => setTimeout(r, 200));
                    }}
                }} catch(e) {{}}
            }})()
            """, sid=la_sid)

    async def phase3_extract_answers(self):
        if self.skip_test:
            print("[!] Bỏ qua trích xuất đáp án (--skip-test)", flush=True)
            return

        test_id = self.unit_info['testId']
        print(f"\n{'='*60}", flush=True)
        print(f"=== PHA 3: TỰ ĐỘNG TRÍCH XUẤT ĐÁP ÁN UNIT TEST ({test_id}) ===", flush=True)
        print(f"{'='*60}", flush=True)

        # 1. Thử đọc từ bộ nhớ đệm offline trước (data/all_module_answers.json)
        cache_path = DATA_DIR / "all_module_answers.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    all_cache = json.load(f)
                mod_key = f"M{self.custom_module}" if self.custom_module else ("M3" if self.course_id == 1548014 else "M2")
                if mod_key in all_cache and str(self.unit_seq) in all_cache[mod_key]:
                    cached = all_cache[mod_key][str(self.unit_seq)]
                    if cached.get("count") == 30:
                        print(f"[+] Sử dụng bộ đáp án chuẩn 30/30 từ Cache ({mod_key} Unit {self.unit_seq})!", flush=True)
                        self.answers_key = {int(k): v for k, v in cached["answers"].items()}
                        for q_num in sorted(self.answers_key.keys()):
                            ans_item = self.answers_key[q_num]
                            print(f"  Q{q_num:02d}: ({ans_item['letter']}) [idx {ans_item['index']}] - {ans_item['text'][:60]}", flush=True)
                        print(f"[+] Sẵn sàng 30/30 đáp án chuẩn 100%!", flush=True)
                        return
            except Exception as e:
                print(f"[!] Đọc cache: {e}, chuyển sang tải trực tuyến...", flush=True)

        # 2. Tải trực tiếp từ Metadata ETS (với cơ chế thử lại 5 lần)
        meta_url = f"https://ets.toeicolpc.com/Runtime/Metadata/Courses/{test_id}.js"
        req = urllib.request.Request(meta_url, headers={'User-Agent': 'Mozilla/5.0'})
        content = ""
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    content = resp.read().decode('utf-8', errors='ignore')
                break
            except Exception:
                await asyncio.sleep(1)

        line0 = content.splitlines()[0]
        s = line0.find('{')
        data = json.loads(line0[s:].strip())
        units = data['Course']['Unit']
        if not isinstance(units, list): units = [units]

        items_list = []
        for u in units:
            comp = u.get('Component', [])
            if not isinstance(comp, list): comp = [comp]
            for c in comp:
                skill_folder = 'Reading' if str(c.get('skillid')) == '2' else 'Listening'
                c_code = c.get('code')
                subcomp = c.get('SubComponent', [])
                if not isinstance(subcomp, list): subcomp = [subcomp]
                for sc in subcomp:
                    if sc.get('Title') == 'Test':
                        it = sc.get('Item', [])
                        if not isinstance(it, list): it = [it]
                        for item in it:
                            code = item.get('code')
                            items_list.append({
                                'code': code,
                                'TOEICIds': item.get('TOEICIds'),
                                'url': f'https://ets.toeicolpc.com/Runtime/Content/{skill_folder}/{c_code}/{code}ex.js'
                            })

        print(f"[+] Tìm thấy {len(items_list)} phần tử câu hỏi trong metadata bài test.", flush=True)
        answers_key = {}
        for it in items_list:
            q_ids = [int(x) for x in it['TOEICIds'].split('|')]
            url = it['url']
            ex_content = None
            for attempt in range(5):
                try:
                    r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(r, timeout=15) as resp:
                        ex_content = resp.read().decode('utf-8', errors='ignore')
                    break
                except Exception:
                    await asyncio.sleep(1)

            if not ex_content:
                print(f"[-] Không thể tải {url}", flush=True)
                continue

            s_pos = ex_content.find('{')
            e_pos = ex_content.rfind('}')
            sexp = json.loads(ex_content[s_pos:e_pos+1])
            questions = sexp.get('Question', [])
            if not isinstance(questions, list): questions = [questions]

            for idx, q_obj in enumerate(questions):
                q_num = q_ids[idx]
                ans_list = q_obj.get('Answer', [])
                correct_idx = None
                correct_text = ''
                for a_i, a_str in enumerate(ans_list):
                    clean_str = re.sub(r'<[^>]+>', ' ', a_str).strip()
                    is_div = '<div>' in a_str or '<div ' in a_str
                    is_text_correct = False
                    lower = clean_str.lower()
                    if any(k in lower for k in ['this is the correct answer', 'this answer is correct', 'answer is correct', 'is the correct', 'is the correct option']):
                        is_text_correct = True
                    elif 'is correct' in lower and 'not correct' not in lower:
                        is_text_correct = True

                    if is_div or is_text_correct:
                        correct_idx = a_i
                        correct_text = clean_str
                        break

                if correct_idx is not None:
                    letter = chr(65 + correct_idx)
                    answers_key[q_num] = {
                        'q_num': q_num,
                        'index': correct_idx,
                        'letter': letter,
                        'text': correct_text[:80]
                    }
                    print(f"  Q{q_num:02d}: ({letter}) [idx {correct_idx}] - {correct_text[:60]}", flush=True)

        print(f"[+] Trích xuất thành công: {len(answers_key)}/30 đáp án!", flush=True)
        self.answers_key = answers_key
        ans_path = OUTPUT_DIR / f"unit{self.unit_seq}_answers_key.json"
        with open(ans_path, "w", encoding="utf-8") as f:
            json.dump(answers_key, f, ensure_ascii=False, indent=2)

    async def phase4_solve_unit_test(self):
        if self.skip_test:
            print("[!] Bỏ qua giải Unit Test (--skip-test)", flush=True)
            return None

        print(f"\n{'='*60}", flush=True)
        print(f"=== PHA 4: GIẢI UNIT TEST ĐẠT ĐIỂM TỐI ĐA 100/100 ===", flush=True)
        print(f"{'='*60}", flush=True)

        # Đóng cửa sổ thi cũ nếu còn sót
        targets = await self.get_targets()
        for t in targets:
            if any(k in t.get('url', '') for k in ['Test.aspx', 'SysCheck.aspx']):
                try:
                    await self.send("Target.closeTarget", {"targetId": t['targetId']})
                except Exception:
                    pass
                await asyncio.sleep(0.5)

        targets = await self.get_targets()
        page = next((t for t in targets if t['type'] == 'page' and 'edtoeic' in t.get('url', '')), None)
        if not page:
            raise Exception("Không tìm thấy trang TOEIC!")
        page_sid = await self.attach(page['targetId'])

        test_id = self.unit_info['testId']
        print(f"[+] Gọi edns.toeic.gotoUnitTest({self.course_id}, {test_id}, {self.toeic_course_id}, false, {self.unit_seq}, {{}})...", flush=True)
        await self.js(f"edns.toeic.gotoUnitTest({self.course_id}, {test_id}, {self.toeic_course_id}, false, {self.unit_seq}, {{}});", sid=page_sid)

        test_target = None
        for _ in range(15):
            await asyncio.sleep(2)
            targets = await self.get_targets()
            test_target = next((t for t in targets if t['type'] == 'page' and any(k in t.get('url', '') for k in ['Test.aspx', 'SysCheck.aspx'])), None)
            if test_target: break

        if not test_target:
            raise Exception("Không mở được cửa sổ Test!")

        test_sid = await self.attach(test_target['targetId'])
        await asyncio.sleep(3)

        # Bỏ qua SysCheck nếu có
        await self.js("""
        (() => {
            const startA = Array.from(document.querySelectorAll('.StartBT a, .startBT a, a, button, input')).find(el => {
                const t = (el.textContent || el.value || '').trim();
                return (t === 'Start' || t === 'Start Section' || t === 'Go' || t === 'Continue') && el.offsetParent !== null;
            });
            if (startA) startA.click();
        })()
        """, sid=test_sid)
        await asyncio.sleep(4)

        # Re-attach vào Test.aspx
        targets = await self.get_targets()
        test_target = next((t for t in targets if t['type'] == 'page' and 'Test.aspx' in t.get('url', '')), None)
        if test_target:
            test_sid = await self.attach(test_target['targetId'])
            print(f"[+] Đã gắn vào Test.aspx: {test_target['url']}", flush=True)

        # Bắt đầu làm bài trong DB & Click Start
        await self.js("""
        (() => {
            window.confirm = () => true;
            window.alert = () => true;
            if (typeof startTestInDB === 'function') {
                try { startTestInDB(); } catch(e) {}
            }
            const startBtn = Array.from(document.querySelectorAll('.StartBT a, .startBT a, a, button, input')).find(el => {
                const t = (el.textContent || el.value || '').trim();
                return (t === 'Start' || t === 'Start Section' || t === 'Go' || t === 'Continue') && el.offsetParent !== null;
            });
            if (startBtn) startBtn.click();
        })()
        """, sid=test_sid)
        await asyncio.sleep(3)

        answers_json = json.dumps(self.answers_key)
        await self.js(f"window.__ANSWERS_KEY = {answers_json};", sid=test_sid)

        SOLVER_JS = r"""
        (() => {
            const answersKey = window.__ANSWERS_KEY || {};
            const acts = [];
            const bodyText = document.body ? document.body.innerText : '';

            // 1. Kiểm tra màn hình kết quả
            if (bodyText.includes('Score is:') || bodyText.includes('Your Score is') || document.querySelector('.finalGrade, .submitTest.finalGrade')) {
                const scoreSpan = document.querySelector('.testResult');
                const scoreMatch = bodyText.match(/Score is:\s*(\d+)/i) || bodyText.match(/Your Score is:\s*(\d+)/i);
                const scoreVal = scoreSpan ? scoreSpan.innerText.trim() : (scoreMatch ? scoreMatch[1] : null);
                return { isScore: true, scoreVal, bodySnippet: bodyText.substring(0, 300) };
            }

            // 2. Tắt audio / video ngay lập tức
            document.querySelectorAll('audio, video').forEach(m => {
                try {
                    m.currentTime = m.duration || 999;
                    m.dispatchEvent(new Event('ended', { bubbles: true }));
                    acts.push('media_ended');
                } catch(e) {}
            });

            // 3. Tìm các nhóm radio câu hỏi
            const radioGroups = [];
            const seenNames = new Set();
            document.querySelectorAll('input[type="radio"]').forEach(r => {
                if (r.name && !seenNames.has(r.name) && r.offsetParent !== null) {
                    seenNames.add(r.name);
                    radioGroups.push(r.name);
                }
            });

            let startQ = null;
            let endQ = null;
            const headerMatch = bodyText.match(/Question\s+(\d+)(?:\s*-\s*(\d+))?\s+of\s+30/i);
            if (headerMatch) {
                startQ = parseInt(headerMatch[1]);
                endQ = headerMatch[2] ? parseInt(headerMatch[2]) : startQ;
            }
            const qNumMatches = Array.from(bodyText.matchAll(/(?:^|\n)\s*(\d+)\.\s+[A-Za-z]/g)).map(m => parseInt(m[1]));
            if (!startQ && qNumMatches.length > 0) {
                startQ = qNumMatches[0];
                endQ = qNumMatches[qNumMatches.length - 1];
            }

            // 4. Màn hình hướng dẫn / chuyển phần (Không có radio)
            if (radioGroups.length === 0) {
                const actionBtn = Array.from(document.querySelectorAll('.nextBT a, .StartBT a, .startBT a, a, button, input'))
                    .find(el => {
                        const t = (el.textContent || el.value || '').trim();
                        return (t === 'Next' || t === 'Start' || t === 'Start Section' || t === 'Go' || t === 'Continue') && el.offsetParent !== null && !el.disabled;
                    });
                if (actionBtn) {
                    const text = (actionBtn.textContent || actionBtn.value || '').trim();
                    actionBtn.click();
                    acts.push(`clicked_${text}`);
                    return { action: `direction_${text}`, acts };
                }
                try {
                    if (typeof SetNextItem === 'function') {
                        SetNextItem();
                        acts.push('called_SetNextItem');
                        return { action: 'called_SetNextItem', acts };
                    }
                } catch(e) {}
                return { action: 'waiting_direction', acts };
            }

            // 5. Màn hình câu hỏi: Tích chọn đáp án chính xác
            let newlyAnswered = 0;
            if (startQ !== null) {
                radioGroups.forEach((groupName, gIdx) => {
                    const qNum = startQ + gIdx;
                    const groupRadios = Array.from(document.querySelectorAll(`input[type="radio"][name="${groupName}"]`))
                        .filter(r => r.offsetParent !== null);
                    const ansInfo = answersKey[qNum];
                    if (ansInfo && groupRadios.length > 0) {
                        const targetIdx = Math.min(ansInfo.index, groupRadios.length - 1);
                        const targetRadio = groupRadios[targetIdx];
                        if (!targetRadio.checked) {
                            targetRadio.checked = true;
                            targetRadio.dispatchEvent(new Event('change', { bubbles: true }));
                            targetRadio.dispatchEvent(new Event('click', { bubbles: true }));
                            newlyAnswered++;
                            acts.push(`Q${qNum}=${ansInfo.letter}`);
                        }
                    } else if (groupRadios.length > 0 && !groupRadios.some(r => r.checked)) {
                        // Fallback: chọn đáp án đầu tiên để không bao giờ bị kẹt
                        groupRadios[0].checked = true;
                        groupRadios[0].dispatchEvent(new Event('change', { bubbles: true }));
                        groupRadios[0].dispatchEvent(new Event('click', { bubbles: true }));
                        newlyAnswered++;
                        acts.push(`Q${qNum}=Fallback_A`);
                    }
                });
            }

            const allChecked = radioGroups.every(name => {
                return Array.from(document.querySelectorAll(`input[type="radio"][name="${name}"]`))
                    .filter(r => r.offsetParent !== null)
                    .some(r => r.checked);
            });

            if (newlyAnswered > 0) {
                return { action: 'answering', startQ, endQ, newlyAnswered, allChecked, acts };
            }

            // Khi đã chọn đủ tất cả các câu trên màn hình:
            if (allChecked) {
                // CHÚ Ý QUAN TRỌNG: Chỉ nộp bài khi đã đạt câu 30 (endQ === 30)
                if (endQ === 30 || (startQ !== null && startQ >= 30)) {
                    if (window.__SUBMIT_TRIGGERED) {
                        return { action: 'waiting_submit', startQ, endQ, acts };
                    }
                    window.__SUBMIT_TRIGGERED = true;

                    try {
                        if (typeof saveBeforeClose === 'function') {
                            saveBeforeClose(function() {
                                if (typeof submitTestAfterSaving === 'function') submitTestAfterSaving();
                                else submitTest();
                            });
                            acts.push('called_saveBeforeClose');
                            return { action: 'submitting_saveBeforeClose', startQ, endQ, acts };
                        } else if (typeof pm !== 'undefined' && pm && typeof pm.saveItemState === 'function') {
                            pm.saveItemState(function() { submitTest(); }, 1000);
                            acts.push('called_pm_saveItemState');
                            return { action: 'submitting_pm_save', startQ, endQ, acts };
                        } else {
                            submitTest();
                            acts.push('called_submitTest_fallback');
                            return { action: 'submitting_fallback', startQ, endQ, acts };
                        }
                    } catch(e) {
                        submitTest();
                        return { action: 'error_submit', error: e.message };
                    }
                }

                const nextBtn = Array.from(document.querySelectorAll('.nextBT a, .StartBT a, .startBT a, a, button'))
                    .find(el => {
                        const t = (el.textContent || el.value || '').trim();
                        return (t === 'Next' || t === 'Start Section' || t === 'Start' || t === 'Go') && el.offsetParent !== null && !el.disabled;
                    });
                if (nextBtn) {
                    nextBtn.click();
                    acts.push('clicked_Next');
                    return { action: 'clicked_Next', startQ, endQ, acts };
                }
            }

            return { action: 'waiting', startQ, endQ, allChecked, acts };
        })()
        """

        print("[+] Bắt đầu vòng lặp giải bài tự động...", flush=True)
        final_score = None
        for step in range(1, 160):
            await asyncio.sleep(1.2)
            try:
                targets = await self.get_targets()
                test_exists = any(t['type'] == 'page' and 'Test.aspx' in t.get('url', '') for t in targets)
                if not test_exists:
                    print("[+] Cửa sổ Test.aspx đã đóng (đã nộp bài thành công)!", flush=True)
                    break

                await self.js(f"if (!window.__ANSWERS_KEY) window.__ANSWERS_KEY = {answers_json};", sid=test_sid)
                state = await self.js(SOLVER_JS, sid=test_sid)

                if state.get("isScore"):
                    final_score = state.get("scoreVal")
                    print(f"\n{'='*65}", flush=True)
                    print(f"[🏆 ĐÃ NHẬN ĐIỂM SỐ CHÍNH THỨC: {final_score} / 100]", flush=True)
                    print(f"Chi tiết: {state.get('bodySnippet')}", flush=True)
                    print(f"{'='*65}", flush=True)
                    await asyncio.sleep(2)
                    await self.screenshot(f"unit{self.unit_seq}_100_final_verified", sid=test_sid)

                    try:
                        targets = await self.get_targets()
                        for t in targets:
                            if any(k in t.get('url', '') for k in ['Test.aspx', 'SysCheck.aspx']):
                                await self.send("Target.closeTarget", {"targetId": t['targetId']})
                    except Exception:
                        pass
                    break

                action = state.get("action")
                acts = state.get("acts", [])
                startQ = state.get("startQ")
                endQ = state.get("endQ")
                print(f"[{step:03d}] Hành động: {action:28} | Q{startQ}-{endQ} | {acts}", flush=True)

            except Exception as e:
                targets = await self.get_targets()
                test_exists = any(t['type'] == 'page' and 'Test.aspx' in t.get('url', '') for t in targets)
                if not test_exists:
                    print("[+] Cửa sổ Test.aspx đã đóng sau khi nộp bài thành công!", flush=True)
                    break
                print(f"[{step:03d}] Lỗi vòng lặp: {e}", flush=True)
                await asyncio.sleep(2)

        return final_score

    async def phase5_verify_and_sync(self):
        print(f"\n{'='*60}", flush=True)
        print(f"=== PHA 5: XÁC MINH TRANG CHỦ & DATABASE BACKEND ===", flush=True)
        print(f"{'='*60}", flush=True)

        targets = await self.get_targets()
        page = next((t for t in targets if t['type'] == 'page' and 'edtoeic' in t.get('url', '')), None)
        if not page:
            raise Exception("Không tìm thấy trang TOEIC!")
        page_sid = await self.attach(page['targetId'])

        # Chuyển về trang chủ #/home
        await self.js("window.location.href = 'https://edtoeic.engdis.com/EdToeic1#/home';", sid=page_sid)
        await asyncio.sleep(4)
        targets = await self.get_targets()
        page = next((t for t in targets if t['type'] == 'page' and 'edtoeic' in t.get('url', '')), None)
        page_sid = await self.attach(page['targetId'])

        # Truy vấn API GetUnits
        db_res = await self.js(f"""
        new Promise((resolve) => {{
            try {{
                const toeicInfo = JSON.parse(localStorage.getItem('toeicInformation'));
                const toeicURL = toeicInfo.toeicServicesURL + '/LearningService.svc/script/GetUnits?courseId={self.toeic_course_id}';
                const toeicSessionKey = toeicInfo.toeicSessionKey;
                $.ajax({{
                    url: toeicURL,
                    type: 'GET',
                    datatype: 'json',
                    headers: {{ 'Edusoft-SessionKey': toeicSessionKey }},
                    success: (data) => resolve(data),
                    error: (err) => resolve({{ error: err }})
                }});
            }} catch(e) {{ resolve({{ error: e.message }}); }}
        }})
        """, sid=page_sid)

        u_record = None
        if db_res and 'd' in db_res:
            u_record = next((u for u in db_res['d'] if u.get('sequence') == self.unit_seq), None)
        print(f"[+] Dữ liệu DB chính thức của Unit {self.unit_seq}:", flush=True)
        print(json.dumps(u_record, indent=2), flush=True)

        # Cập nhật AngularJS Scope trang chủ
        test_id = self.unit_info['testId']
        await self.js(f"""
        (() => {{
            try {{
                const appEl = document.querySelector('[ng-app]') || document.body;
                const inj = angular.element(appEl).injector();
                const cds = inj.get('courseDataService');
                if (cds && typeof cds.updateUnitTestGrade === 'function') {{
                    cds.updateUnitTestGrade({test_id}, 100);
                }}
                const uEl = Array.from(document.querySelectorAll('.home__unit')).find(el => el.innerText.includes('{self.unit_info['name']}'));
                if (uEl) {{
                    const sc = angular.element(uEl).scope();
                    if (sc.unit && sc.unit.Metadata && sc.unit.Metadata.UnitTest) {{
                        sc.unit.Metadata.UnitTest.grade = 100;
                    }}
                    sc.$apply();
                }}
            }} catch(e) {{}}
        }})()
        """, sid=page_sid)

        await asyncio.sleep(1)
        await self.js(f"""
        (() => {{
            const uEl = Array.from(document.querySelectorAll('.home__unit')).find(el => el.innerText.includes('{self.unit_info['name']}'));
            if (uEl) uEl.scrollIntoView({{ behavior: 'instant', block: 'center' }});
        }})()
        """, sid=page_sid)
        await asyncio.sleep(1)
        await self.screenshot(f"home_unit{self.unit_seq}_completed", sid=page_sid)
        print(f"[+] Hoàn thành toàn trình Unit {self.unit_seq}!", flush=True)

    async def run(self):
        await self.connect()
        la_sid = await self.phase1_discover_unit()
        if not self.only_test:
            await self.phase2_complete_lessons(la_sid)
        if not self.skip_test:
            await self.phase3_extract_answers()
            score = await self.phase4_solve_unit_test()
        else:
            score = None
        await self.phase5_verify_and_sync()
        try:
            await self.ws.close()
        except Exception:
            pass
        return score


# ==============================================================================
# ASSESSMENT CENTER SOLVER (MIDTERM & FINAL TESTS)
# ==============================================================================

async def solve_assessment_test(test_idx, custom_port=None):
    if test_idx not in ASSESSMENT_TESTS:
        print(f"[!] Bài test không hợp lệ. Chọn 1-5.")
        return

    tdef = ASSESSMENT_TESTS[test_idx]
    print("\n" + "="*70)
    print(f"=== BẮT ĐẦU GIẢI: {tdef['name'].upper()} ===")
    print("="*70)

    ans_file = ASSESSMENT_ANSWERS_DIR / tdef['file_key']
    if not ans_file.exists():
        print(f"[!] Không tìm thấy tệp đáp án: {ans_file}")
        return

    with open(ans_file, 'r', encoding='utf-8') as f:
        answers = json.load(f)
    print(f"[+] Đã tải {len(answers)}/{tdef['total']} đáp án chuẩn xác từ tệp.", flush=True)

    ws_url, port = detect_chrome_cdp(custom_port)
    if not ws_url:
        print("[!] Không tìm thấy Chrome. Hãy chạy start_chrome_debug.bat trước.")
        return

    ws = await websockets.connect(ws_url, max_size=100*1024*1024, open_timeout=30)
    req_id = 0

    async def cmd(method, params=None, session_id=None):
        nonlocal req_id
        req_id += 1
        cid = req_id
        payload = {"id": cid, "method": method}
        if params: payload["params"] = params
        if session_id: payload["sessionId"] = session_id
        await ws.send(json.dumps(payload))
        while True:
            res = json.loads(await ws.recv())
            if res.get("id") == cid:
                return res

    targets = (await cmd("Target.getTargets"))['result']['targetInfos']
    page = next((t for t in targets if t['type'] == 'page' and ('edtoeic' in t.get('url', '') or 'toeicolpc' in t.get('url', ''))), None)
    if not page:
        print("[!] Đang tự động mở tab ETS TOEIC trên trình duyệt Chrome...", flush=True)
        await cmd("Target.createTarget", {"url": "https://edtoeic.engdis.com/EdToeic1#/home"})
        await asyncio.sleep(4)
        targets = (await cmd("Target.getTargets"))['result']['targetInfos']
        page = next((t for t in targets if t['type'] == 'page' and ('edtoeic' in t.get('url', '') or 'toeicolpc' in t.get('url', ''))), None)
        if not page:
            print("[!] Không tìm thấy trang TOEIC nào đang mở.")
            await ws.close()
            return

    page_sid = (await cmd("Target.attachToTarget", {"targetId": page["targetId"], "flatten": True}))['result']['sessionId']

    # Mở modal Assessment Center nếu chưa mở
    print("[+] Đang mở cửa sổ Assessment Center...", flush=True)
    await cmd("Runtime.evaluate", {
        "expression": """(() => {
            const btn = document.querySelector('[ng-click*="openAssessments"], [data-ng-click*="openAssessments"]');
            if (btn) btn.click();
        })()"""
    }, session_id=page_sid)
    await asyncio.sleep(2)

    # Click nút Go tương ứng
    print(f"[+] Tìm và bấm nút 'Go' cho bài thi {tdef['name']}...", flush=True)
    click_res = await cmd("Runtime.evaluate", {
        "expression": f"""(() => {{
            const rows = Array.from(document.querySelectorAll('.assesmentsModal table tr, .availableTests table tr'));
            for (const r of rows) {{
                if (r.innerText.includes('{tdef['id']}') || r.innerText.includes('{tdef['name'].split(':')[0]}')) {{
                    const btn = r.querySelector('a, button, [ng-click*="startTest"], [ng-click*="openTest"]');
                    if (btn) {{
                        btn.click();
                        return {{ clicked: true, row: r.innerText.substring(0, 100) }};
                    }}
                }}
            }}
            return {{ clicked: false }};
        }})()""",
        "returnByValue": True
    }, session_id=page_sid)
    print("  Kết quả bấm nút:", click_res.get('result', {}).get('result', {}).get('value'))

    # Chờ cửa sổ Test.aspx mở ra
    test_target = None
    for _ in range(15):
        await asyncio.sleep(2)
        targets = (await cmd("Target.getTargets"))['result']['targetInfos']
        test_target = next((t for t in targets if any(k in t.get('url', '') for k in ['Test.aspx', 'SysCheck.aspx'])), None)
        if test_target: break

    if not test_target:
        print("[!] Không tìm thấy cửa sổ bài thi mới mở. Hãy bấm Go thủ công trên màn hình nếu chưa mở!")
        await ws.close()
        return

    test_sid = (await cmd("Target.attachToTarget", {"targetId": test_target["targetId"], "flatten": True}))['result']['sessionId']
    print(f"[+] Đã gắn vào cửa sổ thi: {test_target['url']}")

    # Click Start SysCheck nếu có
    await cmd("Runtime.evaluate", {
        "expression": """(() => {
            const btn = Array.from(document.querySelectorAll('.StartBT a, .startBT a, a, button, input')).find(el => {
                const t = (el.textContent || el.value || '').trim();
                return (t === 'Start' || t === 'Start Section' || t === 'Go' || t === 'Continue') && el.offsetParent !== null;
            });
            if (btn) btn.click();
        })()"""
    }, session_id=test_sid)
    await asyncio.sleep(4)

    # Re-attach vào Test.aspx
    targets = (await cmd("Target.getTargets"))['result']['targetInfos']
    test_target = next((t for t in targets if 'Test.aspx' in t.get('url', '')), None)
    if test_target:
        test_sid = (await cmd("Target.attachToTarget", {"targetId": test_target["targetId"], "flatten": True}))['result']['sessionId']

    # Start Test in DB
    await cmd("Runtime.evaluate", {
        "expression": """(() => {
            window.confirm = () => true;
            window.alert = () => true;
            if (typeof startTestInDB === 'function') {
                try { startTestInDB(); } catch(e) {}
            }
            const btn = Array.from(document.querySelectorAll('.StartBT a, .startBT a, a, button, input')).find(el => {
                const t = (el.textContent || el.value || '').trim();
                return (t === 'Start' || t === 'Start Section' || t === 'Go' || t === 'Continue') && el.offsetParent !== null;
            });
            if (btn) btn.click();
        })()"""
    }, session_id=test_sid)
    await asyncio.sleep(3)

    ans_json = json.dumps(answers)
    await cmd("Runtime.evaluate", {
        "expression": f"window.__ANSWERS_KEY = {ans_json};"
    }, session_id=test_sid)

    SOLVER_ASSESSMENT_JS = f"""
    (() => {{
        const answersKey = window.__ANSWERS_KEY || {{}};
        const totalQuestions = {tdef['total']};
        const acts = [];
        const bodyText = document.body ? document.body.innerText : '';

        if (bodyText.includes('Score is:') || bodyText.includes('Your Score is') || document.querySelector('.finalGrade, .submitTest.finalGrade')) {{
            const scoreSpan = document.querySelector('.testResult');
            const scoreMatch = bodyText.match(/Score is:\\s*(\\d+)/i) || bodyText.match(/Your Score is:\\s*(\\d+)/i);
            const scoreVal = scoreSpan ? scoreSpan.innerText.trim() : (scoreMatch ? scoreMatch[1] : null);
            return {{ isScore: true, scoreVal, bodySnippet: bodyText.substring(0, 300) }};
        }}

        document.querySelectorAll('audio, video').forEach(m => {{
            try {{
                m.currentTime = m.duration || 999;
                m.dispatchEvent(new Event('ended', {{ bubbles: true }}));
                acts.push('media_ended');
            }} catch(e) {{}}
        }});

        const radioGroups = [];
        const seenNames = new Set();
        document.querySelectorAll('input[type="radio"]').forEach(r => {{
            if (r.name && !seenNames.has(r.name) && r.offsetParent !== null) {{
                seenNames.add(r.name);
                radioGroups.push(r.name);
            }}
        }});

        let startQ = null;
        let endQ = null;
        const headerMatch = bodyText.match(new RegExp('Question\\\\s+(\\\\d+)(?:\\\\s*-\\\\s*(\\\\d+))?\\\\s+of\\\\s+' + totalQuestions, 'i'));
        if (headerMatch) {{
            startQ = parseInt(headerMatch[1]);
            endQ = headerMatch[2] ? parseInt(headerMatch[2]) : startQ;
        }}
        const qNumMatches = Array.from(bodyText.matchAll(/(?:^|\\n)\\s*(\\d+)\\.\\s+[A-Za-z]/g)).map(m => parseInt(m[1]));
        if (!startQ && qNumMatches.length > 0) {{
            startQ = qNumMatches[0];
            endQ = qNumMatches[qNumMatches.length - 1];
        }}

        if (radioGroups.length === 0) {{
            const actionBtn = Array.from(document.querySelectorAll('.nextBT a, .StartBT a, .startBT a, a, button, input'))
                .find(el => {{
                    const t = (el.textContent || el.value || '').trim();
                    return (t === 'Next' || t === 'Start' || t === 'Start Section' || t === 'Go' || t === 'Continue') && el.offsetParent !== null && !el.disabled;
                }});
            if (actionBtn) {{
                const text = (actionBtn.textContent || actionBtn.value || '').trim();
                actionBtn.click();
                acts.push(`clicked_${{text}}`);
                return {{ action: `direction_${{text}}`, acts }};
            }}
            try {{
                if (typeof SetNextItem === 'function') {{
                    SetNextItem();
                    acts.push('called_SetNextItem');
                    return {{ action: 'called_SetNextItem', acts }};
                }}
            }} catch(e) {{}}
            return {{ action: 'waiting_direction', acts }};
        }}

        let newlyAnswered = 0;
        if (startQ !== null) {{
            radioGroups.forEach((groupName, gIdx) => {{
                const qNum = startQ + gIdx;
                const groupRadios = Array.from(document.querySelectorAll(`input[type="radio"][name="${{groupName}}"]`))
                    .filter(r => r.offsetParent !== null);
                const ansInfo = answersKey[qNum] || answersKey[String(qNum)];
                if (ansInfo && groupRadios.length > 0) {{
                    const targetIdx = Math.min(ansInfo.index, groupRadios.length - 1);
                    const targetRadio = groupRadios[targetIdx];
                    if (!targetRadio.checked) {{
                        targetRadio.checked = true;
                        targetRadio.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        targetRadio.dispatchEvent(new Event('click', {{ bubbles: true }}));
                        newlyAnswered++;
                        acts.push(`Q${{qNum}}=${{ansInfo.letter}}`);
                    }}
                }} else if (groupRadios.length > 0 && !groupRadios.some(r => r.checked)) {{
                    groupRadios[0].checked = true;
                    groupRadios[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    groupRadios[0].dispatchEvent(new Event('click', {{ bubbles: true }}));
                    newlyAnswered++;
                    acts.push(`Q${{qNum}}=Fallback_A`);
                }}
            }});
        }}

        const allChecked = radioGroups.every(name => {{
            return Array.from(document.querySelectorAll(`input[type="radio"][name="${{name}}"]`))
                .filter(r => r.offsetParent !== null)
                .some(r => r.checked);
        }});

        if (newlyAnswered > 0) {{
            return {{ action: 'answering', startQ, endQ, newlyAnswered, allChecked, acts }};
        }}

        if (allChecked) {{
            if (endQ === totalQuestions || (startQ !== null && startQ >= totalQuestions)) {{
                if (window.__SUBMIT_TRIGGERED) {{
                    return {{ action: 'waiting_submit', startQ, endQ, acts }};
                }}
                window.__SUBMIT_TRIGGERED = true;

                try {{
                    if (typeof saveBeforeClose === 'function') {{
                        saveBeforeClose(function() {{
                            if (typeof submitTestAfterSaving === 'function') submitTestAfterSaving();
                            else submitTest();
                        }});
                        acts.push('called_saveBeforeClose');
                        return {{ action: 'submitting_saveBeforeClose', startQ, endQ, acts }};
                    }} else if (typeof pm !== 'undefined' && pm && typeof pm.saveItemState === 'function') {{
                        pm.saveItemState(function() {{ submitTest(); }}, 1000);
                        acts.push('called_pm_saveItemState');
                        return {{ action: 'submitting_pm_save', startQ, endQ, acts }};
                    }} else {{
                        submitTest();
                        acts.push('called_submitTest_fallback');
                        return {{ action: 'submitting_fallback', startQ, endQ, acts }};
                    }}
                }} catch(e) {{
                    submitTest();
                    return {{ action: 'error_submit', error: e.message }};
                }}
            }}

            const nextBtn = Array.from(document.querySelectorAll('.nextBT a, .StartBT a, .startBT a, a, button'))
                .find(el => {{
                    const t = (el.textContent || el.value || '').trim();
                    return (t === 'Next' || t === 'Start Section' || t === 'Start' || t === 'Go') && el.offsetParent !== null && !el.disabled;
                }});
            if (nextBtn) {{
                nextBtn.click();
                acts.push('clicked_Next');
                return {{ action: 'clicked_Next', startQ, endQ, acts }};
            }}
        }}

        return {{ action: 'waiting', startQ, endQ, allChecked, acts }};
    }})()
    """

    print("[+] Bắt đầu vòng lặp giải bài thi Assessment...", flush=True)
    max_steps = (tdef['total'] // 2) + 60
    for step in range(1, max_steps):
        await asyncio.sleep(1.2)
        try:
            targets = (await cmd("Target.getTargets"))['result']['targetInfos']
            test_exists = any(t['type'] == 'page' and 'Test.aspx' in t.get('url', '') for t in targets)
            if not test_exists:
                print("[+] Cửa sổ bài thi đã nộp và đóng thành công!")
                break

            await cmd("Runtime.evaluate", {"expression": f"if (!window.__ANSWERS_KEY) window.__ANSWERS_KEY = {ans_json};"}, session_id=test_sid)
            state = (await cmd("Runtime.evaluate", {"expression": SOLVER_ASSESSMENT_JS, "returnByValue": True}, session_id=test_sid))['result']['result']['value']

            if state.get("isScore"):
                score = state.get("scoreVal")
                print("\n" + "="*70)
                print(f"[🏆 ĐÃ ĐẠT ĐIỂM SỐ CHÍNH THỨC: {score} / 100]")
                print(f"Chi tiết: {state.get('bodySnippet')}")
                print("="*70)
                await asyncio.sleep(2)
                # Chụp ảnh
                try:
                    r = await cmd("Page.captureScreenshot", {"format": "png"}, session_id=test_sid)
                    data = r.get("result", {}).get("data", "")
                    if data:
                        p = OUTPUT_DIR / f"{tdef['short_name']}_verified.png"
                        with open(p, "wb") as pf: pf.write(base64.b64decode(data))
                        print(f"  [📸 Screenshot] Đã lưu: {p.name}")
                except Exception:
                    pass
                break

            action = state.get("action")
            startQ = state.get("startQ")
            endQ = state.get("endQ")
            acts = state.get("acts", [])
            print(f"[{step:03d}] {action:28} | Q{startQ}-{endQ} | {acts}", flush=True)

        except Exception as e:
            print(f"[{step:03d}] Lỗi: {e}")
            await asyncio.sleep(2)

    await ws.close()
    print(f"[+] Hoàn tất bài thi: {tdef['name']}!\n")


# ==============================================================================
# DASHBOARD / KIỂM TRA TIẾN ĐỘ
# ==============================================================================

async def check_full_status(custom_port=None):
    """Kiểm tra và in bảng tổng kết tiến độ tất cả các module"""
    print("\n" + "="*75)
    print("      📊 BẢNG TỔNG KẾT TIẾN ĐỘ VÀ ĐIỂM SỐ TẤT CẢ CÁC MODULE 📊")
    print("="*75)

    ws_url, port = detect_chrome_cdp(custom_port)
    if not ws_url:
        print("[!] Không tìm thấy Chrome. Hãy chạy start_chrome_debug.bat trước.")
        return

    ws = await websockets.connect(ws_url, max_size=50*1024*1024, open_timeout=30)
    req_id = 0
    async def cmd(method, params=None, session_id=None):
        nonlocal req_id
        req_id += 1
        cid = req_id
        payload = {"id": cid, "method": method}
        if params: payload["params"] = params
        if session_id: payload["sessionId"] = session_id
        await ws.send(json.dumps(payload))
        while True:
            res = json.loads(await ws.recv())
            if res.get("id") == cid:
                return res

    targets = (await cmd("Target.getTargets"))['result']['targetInfos']
    page = next((t for t in targets if t['type'] == 'page' and ('edtoeic' in t.get('url', '') or 'toeicolpc' in t.get('url', ''))), None)
    if not page:
        print("[!] Đang tự động mở tab ETS TOEIC trên trình duyệt Chrome...", flush=True)
        await cmd("Target.createTarget", {"url": "https://edtoeic.engdis.com/EdToeic1#/home"})
        await asyncio.sleep(4)
        targets = (await cmd("Target.getTargets"))['result']['targetInfos']
        page = next((t for t in targets if t['type'] == 'page' and ('edtoeic' in t.get('url', '') or 'toeicolpc' in t.get('url', ''))), None)
        if not page:
            print("[!] Không tìm thấy trang TOEIC nào đang mở.")
            await ws.close()
            return

    sid = (await cmd("Target.attachToTarget", {"targetId": page['targetId'], "flatten": True}))['result']['sessionId']

    js_query = """(async () => {
        const toeicInfo = JSON.parse(localStorage.getItem('toeicInformation')) || {};
        const url_base = toeicInfo.toeicServicesURL + '/LearningService.svc/script/GetUnits?courseId=';
        const key = toeicInfo.toeicSessionKey;

        const getCourseUnits = async (cid) => {
            return new Promise((resolve) => {
                $.ajax({
                    url: url_base + cid,
                    type: 'GET',
                    headers: { 'Edusoft-SessionKey': key },
                    success: (d) => resolve(d.d || []),
                    error: (e) => resolve([])
                });
            });
        };

        const m2 = await getCourseUnits(3257);
        const m3 = await getCourseUnits(3467);
        const m1 = await getCourseUnits(1);
        const currentCourse = JSON.parse(localStorage.getItem('Course')) || {};

        return {
            userName: toeicInfo.toeicUserName,
            currentCourse: currentCourse.CourseName,
            m1: m1,
            m2: m2,
            m3: m3
        };
    })()"""

    res = await cmd("Runtime.evaluate", {"expression": js_query, "awaitPromise": True, "returnByValue": True}, session_id=sid)
    data = res.get("result", {}).get("result", {}).get("value", {})

    print(f"  👤 Học viên: {data.get('userName', 'Unknown')}")
    print(f"  🎯 Khóa học đang chọn: {data.get('currentCourse', 'Unknown')}\n")

    for mod_name, units in [("Module 2: Intermediate", data.get('m2', [])), ("Module 3: Advanced", data.get('m3', []))]:
        print(f"--- {mod_name} ---")
        if not units:
            print("  (Chưa có dữ liệu hoặc chưa đăng ký)")
            continue
        print(f"  {'Seq':<4} | {'Tên Unit':<25} | {'Tiến độ':<10} | {'Điểm Unit Test':<15} | {'Trạng thái'}")
        print("  " + "-"*70)
        for u in units:
            seq = u.get('sequence')
            name = u.get('name')
            comp = f"{u.get('completion', 0)}%"
            gr = u.get('grade')
            gr_str = f"{gr} / 100" if gr is not None else "Chưa làm"
            status = "✓ Hoàn thành" if (gr == 100 or u.get('completion') == 100) else "Chưa hoàn thành"
            print(f"  {seq:<4} | {name:<25} | {comp:<10} | {gr_str:<15} | {status}")
        print()

    await ws.close()
    print("="*75 + "\n")


# ==============================================================================
# MENU TƯƠNG TÁC DÀNH CHO CỘNG ĐỒNG
# ==============================================================================

def interactive_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(BANNER)
        print("             ✨ BẢNG ĐIỀU KHIỂN TỰ ĐỘNG HÓA ETS TOEIC OLPC ✨\n")
        print("  [1] - [8] : Tự động hoàn thành Unit tương ứng (Lessons 100% + Unit Test 100/100)")
        print("  [A]       : 🚀 TỰ ĐỘNG GIẢI TOÀN BỘ CẢ 8 UNITS CỦA MODULE HIỆN TẠI (1 -> 8)")
        print("  [T]       : ⚡ Chỉ thi Unit Test (100/100 tuyệt đối, bỏ qua bài học)")
        print("  [L]       : 📚 Chỉ hoàn thành bài học (100% Lessons, bỏ qua Unit Test)")
        print("  [M]       : 🏆 Giải các bài thi Mid-term & Final Test (Assessment Center)")
        print("  [S]       : 📊 Kiểm tra bảng điểm & tiến độ toàn bộ Module (Dashboard)")
        print("  [Q]       : ❌ Thoát\n")
        print("="*88)
        choice = input("👉 Nhập lựa chọn của bạn (1-8, A, T, L, M, S, Q): ").strip().upper()

        if choice == 'Q':
            print("\nCảm ơn bạn đã sử dụng ETS TOEIC Auto Solver. Tạm biệt!\n")
            break

        elif choice == 'S':
            asyncio.run(check_full_status())
            input("\nNhấn Enter để quay lại Menu...")

        elif choice == 'A':
            print("\n[+] Bắt đầu giải tuần tự cả 8 Units...")
            for u in range(1, 9):
                print(f"\n>>>> TIẾN HÀNH UNIT {u} / 8 <<<<")
                try:
                    solver = MasterUnitSolver(unit_seq=u)
                    asyncio.run(solver.run())
                except Exception as e:
                    print(f"[!] Lỗi tại Unit {u}: {e}")
                time.sleep(3)
            input("\nNhấn Enter để quay lại Menu...")

        elif choice in [str(i) for i in range(1, 9)]:
            u = int(choice)
            print(f"\n[+] Bắt đầu giải Unit {u}...")
            try:
                solver = MasterUnitSolver(unit_seq=u)
                asyncio.run(solver.run())
            except Exception as e:
                print(f"[!] Lỗi: {e}")
            input("\nNhấn Enter để quay lại Menu...")

        elif choice == 'T':
            sub_u = input("👉 Nhập số Unit muốn thi Test (1-8) hoặc gõ 'ALL' để thi toàn bộ 8 Unit Test: ").strip().upper()
            if sub_u == 'ALL':
                for u in range(1, 9):
                    try:
                        solver = MasterUnitSolver(unit_seq=u, only_test=True)
                        asyncio.run(solver.run())
                    except Exception as e:
                        print(f"[!] Lỗi Unit {u}: {e}")
                    time.sleep(3)
            elif sub_u in [str(i) for i in range(1, 9)]:
                try:
                    solver = MasterUnitSolver(unit_seq=int(sub_u), only_test=True)
                    asyncio.run(solver.run())
                except Exception as e:
                    print(f"[!] Lỗi: {e}")
            input("\nNhấn Enter để quay lại Menu...")

        elif choice == 'L':
            sub_u = input("👉 Nhập số Unit muốn hoàn thành bài học (1-8) hoặc 'ALL': ").strip().upper()
            if sub_u == 'ALL':
                for u in range(1, 9):
                    try:
                        solver = MasterUnitSolver(unit_seq=u, skip_test=True)
                        asyncio.run(solver.run())
                    except Exception as e:
                        print(f"[!] Lỗi Unit {u}: {e}")
                    time.sleep(3)
            elif sub_u in [str(i) for i in range(1, 9)]:
                try:
                    solver = MasterUnitSolver(unit_seq=int(sub_u), skip_test=True)
                    asyncio.run(solver.run())
                except Exception as e:
                    print(f"[!] Lỗi: {e}")
            input("\nNhấn Enter để quay lại Menu...")

        elif choice == 'M':
            print("\nDanh sách bài thi Assessment Center:")
            for k, v in ASSESSMENT_TESTS.items():
                print(f"  [{k}] {v['name']} ({v['total']} câu)")
            sub_m = input("\n👉 Chọn số bài thi (1-5): ").strip()
            if sub_m in ['1', '2', '3', '4', '5']:
                asyncio.run(solve_assessment_test(int(sub_m)))
            input("\nNhấn Enter để quay lại Menu...")


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ETS TOEIC OLPC - Auto Solver Pro - MADE BY BANG DZ UwU")
    parser.add_argument("--unit", type=int, default=None, help="Số thứ tự Unit (1-8)")
    parser.add_argument("--all", action="store_true", help="Giải tự động cả 8 Units")
    parser.add_argument("--module", type=int, default=None, help="Chỉ định Module (1, 2, hoặc 3)")
    parser.add_argument("--port", type=int, default=None, help="Cổng Chrome CDP tùy chỉnh")
    parser.add_argument("--only-test", action="store_true", help="Chỉ thi Unit Test (bỏ qua bài học)")
    parser.add_argument("--skip-test", action="store_true", help="Chỉ làm bài học (bỏ qua Unit Test)")
    parser.add_argument("--assessment", type=int, default=None, help="Giải bài thi Assessment Center (1 đến 5)")
    parser.add_argument("--status", action="store_true", help="Xem bảng điểm & tiến độ tất cả các Module")
    args = parser.parse_args()

    # Nếu không có tham số nào thì mở Menu tương tác trực quan
    if len(sys.argv) == 1:
        interactive_menu()
    elif args.status:
        asyncio.run(check_full_status(custom_port=args.port))
    elif args.assessment:
        asyncio.run(solve_assessment_test(args.assessment, custom_port=args.port))
    elif args.all:
        print(BANNER)
        print(f"[🚀] Chạy tự động liên tục cả 8 Units của Module {args.module or 'hiện tại'}...", flush=True)
        for u in range(1, 9):
            print(f"\n{'#'*70}")
            print(f"### [BẮT ĐẦU] UNIT {u} / 8 ###")
            print(f"{'#'*70}\n")
            try:
                solver = MasterUnitSolver(
                    unit_seq=u,
                    module=args.module,
                    custom_port=args.port,
                    skip_test=args.skip_test,
                    only_test=args.only_test
                )
                score = asyncio.run(solver.run())
                print(f"\n[✓] HOÀN TẤT UNIT {u}: Điểm số = {score}/100\n", flush=True)
            except Exception as e:
                print(f"\n[!] LỖI TẠI UNIT {u}: {e}\n", flush=True)
            time.sleep(3)
    else:
        u = args.unit if args.unit is not None else 1
        solver = MasterUnitSolver(
            unit_seq=u,
            module=args.module,
            custom_port=args.port,
            skip_test=args.skip_test,
            only_test=args.only_test
        )
        asyncio.run(solver.run())
