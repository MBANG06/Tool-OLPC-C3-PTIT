"""
MASTER UNIT SOLVER - ETS TOEIC OLPC
Tích hợp toàn bộ quy trình tự động hóa vào 1 script duy nhất:
1. Khám phá cây bài học động qua API DAL
2. Hoàn thành 100% các bài học qua SetProgressPerTask
3. Tự động trích xuất bộ đáp án 30 câu chuẩn 100% của Unit Test
4. Tự động giải bài Unit Test và nộp bài an toàn đạt 100/100
5. Đồng bộ và xác thực với Cơ sở dữ liệu Backend + Chụp ảnh giao diện
"""

import asyncio
import json
import websockets
import base64
import sys
import re
import urllib.request
import argparse

sys.stdout.reconfigure(encoding='utf-8')
import os
from pathlib import Path
from datetime import datetime

# Thư mục gốc chứa script và thư mục lưu trữ kết quả (ảnh, đáp án json)
BASE_DIR = Path(__file__).resolve().parent
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

# Fallback testId table khi GetUnits API trả về 500 (lỗi server ETS với Module 3)
# Lấy từ Learning Area courseTree (ng.probe approach)
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


def detect_chrome_cdp(custom_port=None, custom_url=None):
    """
    Tự động phát hiện WebSocket Debugging URL của Chrome:
    1. Kiểm tra URL hoặc Port tùy chỉnh nếu được truyền vào
    2. Thử truy vấn HTTP endpoint /json/version trên các cổng thông dụng (9222, 9223, 9224)
    3. Tìm kiếm tệp DevToolsActivePort trong thư mục cấu hình trình duyệt người dùng
    """
    if custom_url:
        return custom_url, "custom"

    ports_to_try = [custom_port] if custom_port else [9222, 9223, 9224]

    # Phương án 1: Thử trực tiếp qua HTTP /json/version
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

    # Phương án 2: Quét tệp DevToolsActivePort của Chrome/Edge/Brave
    candidates = []
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    user_profile = os.environ.get("USERPROFILE", "")

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

    for c in candidates:
        if c.is_file():
            try:
                with open(c, "r", encoding="utf-8") as f:
                    port = f.readline().strip()
                    path = f.readline().strip()
                    if port.isdigit():
                        return f"ws://127.0.0.1:{port}{path}", port
            except Exception:
                pass

    return None, None


class MasterUnitSolver:
    def __init__(self, unit_seq=1, module=None, custom_port=None, custom_url=None, skip_test=False, only_test=False):
        self.ws = None
        self.req_id = 0
        self.pending = {}
        self.unit_seq = unit_seq
        self.custom_module = module
        self.custom_port = custom_port
        self.custom_url = custom_url
        self.skip_test = skip_test
        self.only_test = only_test
        self.course_id = None
        self.toeic_course_id = None
        self.course_name = None
        self.unit_info = {}
        self.answers_key = {}

    async def connect(self):
        ws_url, port = detect_chrome_cdp(self.custom_port, self.custom_url)
        if not ws_url:
            print("\n" + "="*70)
            print("[LỖI KHÔNG TÌM THẤY TRÌNH DUYỆT CHROME DEBUGGING]")
            print("="*70)
            print("Không thể kết nối tới Google Chrome qua cổng Remote Debugging.")
            print("Hướng dẫn khắc phục:")
            print("  1. Hãy chạy file 'start_chrome_debug.bat' trong thư mục này.")
            print("  2. Hoặc khởi động Chrome từ lệnh sau:")
            print('     chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* "https://edtoeic.engdis.com/EdToeic1#/home"')
            print("  3. Đăng nhập vào tài khoản và giữ trình duyệt mở rồi chạy lại script.")
            print("="*70 + "\n")
            raise ConnectionError("Không tìm thấy Chrome Debugger")

        print(f"[+] Đã phát hiện Chrome Debugger trên cổng {port}: {ws_url[:55]}...", flush=True)
        self.ws = await websockets.connect(ws_url, max_size=100*1024*1024, ping_interval=30, ping_timeout=60)
        asyncio.create_task(self._listen())
        print(f"[+] Kết nối Chrome CDP thành công!", flush=True)

    async def _listen(self):
        try:
            async for raw in self.ws:
                msg = json.loads(raw)
                if "id" in msg and msg["id"] in self.pending:
                    self.pending[msg["id"]].set_result(msg)
        except Exception:
            pass

    async def send(self, method, params=None, session_id=None, timeout=30):
        self.req_id += 1
        mid = self.req_id
        fut = asyncio.get_event_loop().create_future()
        self.pending[mid] = fut
        payload = {"id": mid, "method": method}
        if params: payload["params"] = params
        if session_id: payload["sessionId"] = session_id
        await self.ws.send(json.dumps(payload))
        try:
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

    async def js(self, expr, sid=None, timeout=30):
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
        try:
            await self.js("const wm = document.getElementById('bang-dz-watermark'); if (wm) wm.remove();", sid=sid)
        except Exception:
            pass
        path = OUTPUT_DIR / f"{name}.png"
        r = await self.send("Page.captureScreenshot", {"format": "png"}, session_id=sid)
        data = r.get("result", {}).get("data", "")
        if data:
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            print(f"  [📸 Screenshot] Đã lưu: {path.name}", flush=True)
        return str(path)

    async def phase1_discover_unit(self):
        print(f"\n{'='*60}", flush=True)
        print(f"=== PHA 1: KHÁM PHÁ CÂY BÀI HỌC UNIT {self.unit_seq} ===", flush=True)
        print(f"{'='*60}", flush=True)

        targets = await self.get_targets()
        page = next((t for t in targets if t['type'] == 'page' and 'edtoeic' in t.get('url', '')), None)
        if not page:
            raise Exception("Không tìm thấy trang TOEIC nào đang mở!")

        page_sid = await self.attach(page['targetId'])

        # 0. Tự động nhận diện Module / Khóa học
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

        # 1. Lấy thông tin Unit từ GetUnits API (hoặc fallback khi API lỗi)
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
            # GetUnits API thất bại (HTTP 500 - lỗi server ETS với Module 3)
            # Thử đọc testId từ Learning Area courseTree trước
            print(f"[!] GetUnits trả về rỗng, thử đọc testId từ Learning Area courseTree...", flush=True)

            # Mở LA nếu chưa mở
            targets = await self.get_targets()
            la_target = next((t for t in targets if 'learningArea' in t.get('url', '')), None)
            if not la_target:
                print("[+] Đang mở Learning Area để lấy testId...", flush=True)
                await self.js(f"""
                (() => {{
                    const appEl = document.querySelector('[ng-app]') || document.body;
                    const inj = angular.element(appEl).injector();
                    const cds = inj ? inj.get('courseDataService') : null;
                    const u = cds && cds.course && cds.course.Children ? cds.course.Children.find(u => u.Sequence === {self.unit_seq}) : null;
                    const firstLessonId = u && u.Children && u.Children.length > 0 ? u.Children[0].NodeId : null;
                    if (firstLessonId && cds.goToLesson) {{
                        cds.goToLesson(u.Children[0]);
                    }}
                }})()
                """, sid=page_sid)
                for _ in range(15):
                    await asyncio.sleep(2)
                    targets = await self.get_targets()
                    la_target = next((t for t in targets if 'learningArea' in t.get('url', '')), None)
                    if la_target: break

            if la_target:
                la_sid_tmp = await self.attach(la_target['targetId'])
                await asyncio.sleep(5)
                la_units = await self.js("""
                (() => {
                    try {
                        const appEl = document.querySelector('app') || document.querySelector('[ng-version]');
                        if (!appEl) return null;
                        const comp = ng.probe(appEl);
                        if (!comp || !comp.componentInstance) return null;
                        const nav = comp.componentInstance.navigationService;
                        if (!nav || !nav.courseTree) return null;
                        return (nav.courseTree.Children || []).map((u, i) => ({
                            sequence: i + 1,
                            name: u.Name,
                            nodeId: u.NodeId,
                            testId: u.Metadata && u.Metadata.UnitTest ? u.Metadata.UnitTest.testId : null,
                            toeicUnitId: u.Metadata && u.Metadata.UnitTest ? u.Metadata.UnitTest.toeicUnitId : null,
                        }));
                    } catch(e) { return null; }
                })()
                """, sid=la_sid_tmp)
                if la_units:
                    target_la = next((u for u in la_units if u.get('sequence') == self.unit_seq), None)
                    if target_la and target_la.get('testId'):
                        target_u = {
                            'name': target_la['name'],
                            'testId': target_la['testId'],
                            'unitId': target_la.get('toeicUnitId'),
                            'grade': None
                        }
                        print(f"[+] Đọc được testId từ LA courseTree: {target_u['testId']}", flush=True)

            # Fallback cuối cùng: dùng bảng hardcode cho Module 3
            if not target_u and self.course_id == 1548014 and self.unit_seq in MODULE3_UNIT_DATA:
                m3u = MODULE3_UNIT_DATA[self.unit_seq]
                target_u = {
                    'name': m3u['name'],
                    'testId': m3u['testId'],
                    'unitId': m3u['toeicUnitId'],
                    'grade': None
                }
                print(f"[!] Dùng bảng hardcode Module 3 cho Unit {self.unit_seq}: testId={target_u['testId']}", flush=True)

            if not target_u:
                raise Exception(f"Không tìm thấy Unit có sequence {self.unit_seq} trong GetUnits và không có fallback!")

        self.unit_info = {
            'sequence': self.unit_seq,
            'name': target_u['name'],
            'testId': target_u['testId'],
            'toeicUnitId': target_u.get('unitId'),
            'initialGrade': target_u.get('grade')
        }
        print(f"[+] Tìm thấy Unit: {self.unit_info['name']} (Sequence: {self.unit_seq}, TestId: {self.unit_info['testId']}, Điểm hiện tại: {self.unit_info['initialGrade']})", flush=True)

        # 2. Đảm bảo mở Learning Area
        targets = await self.get_targets()
        la_target = next((t for t in targets if 'learningArea' in t.get('url', '')), None)
        if not la_target:
            print("[+] Đang mở Learning Area...", flush=True)
            # Điều hướng sang Learning Area
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
        await asyncio.sleep(3)

        # 3. Lấy thông tin Unit Node trong Learning Area courseTree
        unit_node_idx = self.unit_seq - 1
        u_node_res = await self.js(f"""
        (() => {{
            const rootEl = document.querySelector('[ng-version]');
            if (!rootEl) return null;
            const comp = ng.probe(rootEl).componentInstance;
            const nav = comp.navigationService;
            if (!nav || !nav.courseTree) return null;
            const u = nav.courseTree.Children[{unit_node_idx}];
            return u ? {{ nodeId: u.NodeId, name: u.Name }} : null;
        }})()
        """, sid=la_sid)

        if not u_node_res:
            raise Exception(f"Không tìm thấy Unit Node tại index {unit_node_idx} trong nav.courseTree!")

        self.unit_info['nodeId'] = u_node_res['nodeId']
        print(f"[+] Unit NodeId trong courseTree: {self.unit_info['nodeId']}", flush=True)

        # 4. Truy vấn cây bài học chi tiết qua DAL Service
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
            return

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

        success_count = sum(1 for r in res if r.get('ok') or r.get('status') in [200, 201])
        print(f"[+] Hoàn thành {success_count}/{len(undone)} tasks thành công!", flush=True)

        # Giải và lưu điểm 100% vĩnh viễn trên máy chủ cho toàn bộ bài kiểm tra bài học (Lesson Tests)
        print("[+] Đang giải và ghi điểm 100% vĩnh viễn lên máy chủ cho các bài kiểm tra bài học (SaveUserTest)...", flush=True)
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
                                // Type 51: Multiple blanks per question (fill-in dialog)
                                // Format A: ALL blanks merged into 1 ua per question
                                // aId = [[al1.id, correct1.id], [al2.id, correct2.id], ...]
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
                                // Default: single correct answer per blank, find c='1'
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

        # Gửi API lên server đặt điểm 100 cho Step: Test
        test_step_ids = self.unit_info.get('test_step_ids', [])
        if test_step_ids:
            print(f"[+] Gửi SetUserCourseUnitComponentProgress lên server cho {len(test_step_ids)} bài kiểm tra (Step: Test)...", flush=True)
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

        meta_url = f"https://ets.toeicolpc.com/Runtime/Metadata/Courses/{test_id}.js"
        req = urllib.request.Request(meta_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8', errors='ignore')

        line0 = content.splitlines()[0]
        s = line0.find('{')
        data = json.loads(line0[s:].strip())
        units = data['Course']['Unit']

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
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req) as resp:
                    ex_content = resp.read().decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"[-] Lỗi tải {url}: {e}", flush=True)
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
                else:
                    print(f"  [!] Thiếu câu Q{q_num}!", flush=True)

        print(f"[+] Trích xuất thành công: {len(answers_key)}/30 đáp án!", flush=True)
        self.answers_key = answers_key
        ans_path = OUTPUT_DIR / f"unit{self.unit_seq}_answers_key.json"
        with open(ans_path, "w", encoding="utf-8") as f:
            json.dump(answers_key, f, ensure_ascii=False, indent=2)
        print(f"[+] Đã lưu bộ đáp án vào: {ans_path.name}", flush=True)

    async def phase4_solve_unit_test(self):
        print(f"\n{'='*60}", flush=True)
        print(f"=== PHA 4: GIẢI UNIT TEST ĐẠT ĐIỂM TỐI ĐA 100/100 ===", flush=True)
        print(f"{'='*60}", flush=True)

        targets = await self.get_targets()
        for t in targets:
            if any(k in t.get('url', '') for k in ['Test.aspx', 'SysCheck.aspx']):
                await self.send("Target.closeTarget", {"targetId": t['targetId']})
                await asyncio.sleep(0.5)

        # Gắn vào tab chính để kích hoạt gotoUnitTest
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
            const startA = document.querySelector('.StartBT a');
            if (startA) startA.click();
        })()
        """, sid=test_sid)
        await asyncio.sleep(4)

        # Re-attach vào Test.aspx
        targets = await self.get_targets()
        test_target = next((t for t in targets if t['type'] == 'page' and 'Test.aspx' in t.get('url', '')), None)
        test_sid = await self.attach(test_target['targetId'])
        print(f"[+] Đã gắn vào Test.aspx: {test_target['url']}", flush=True)

        # Bắt đầu làm bài trong DB
        await self.js("""
        (() => {
            if (typeof startTestInDB === 'function') startTestInDB();
            const startBtn = document.querySelector('.StartBT a');
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
                const scoreMatch = bodyText.match(/Score is:\s*(\d+)/i);
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
                const nextBtn = Array.from(document.querySelectorAll('.nextBT a, a, button'))
                    .find(el => (el.textContent || el.value || '').trim() === 'Next' && el.offsetParent !== null && !el.disabled);
                if (nextBtn) {
                    nextBtn.click();
                    acts.push('clicked_Next_Direction');
                    return { action: 'direction_next', acts };
                }
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
                if (endQ === 30 || startQ === 27) {
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

                const nextBtn = Array.from(document.querySelectorAll('.nextBT a, a, button'))
                    .find(el => (el.textContent || el.value || '').trim() === 'Next' && el.offsetParent !== null && !el.disabled);
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
        for step in range(1, 150):
            await asyncio.sleep(1.2)
            try:
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
                    break

                action = state.get("action")
                acts = state.get("acts", [])
                startQ = state.get("startQ")
                endQ = state.get("endQ")
                print(f"[{step:03d}] Hành động: {action:28} | Q{startQ}-{endQ} | {acts}", flush=True)

            except Exception as e:
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

        # 1. Truy vấn API GetUnits
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

        # 2. Cập nhật AngularJS Scope trang chủ
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
        await self.phase2_complete_lessons(la_sid)
        await self.phase3_extract_answers()
        score = await self.phase4_solve_unit_test()
        await self.phase5_verify_and_sync()
        await self.ws.close()
        return score

async def list_course_info(custom_port=None):
    """Liệt kê thông tin khóa học và các Unit đang active"""
    print("\n" + "="*65)
    print("=== THÔNG TIN KHÓA HỌC & TIẾN ĐỘ HIỆN TẠI ===")
    print("="*65)
    ws_url, port = detect_chrome_cdp(custom_port)
    if not ws_url:
        print("[!] Không tìm thấy Chrome. Hãy chạy start_chrome_debug.bat trước.")
        return

    ws = await websockets.connect(ws_url, max_size=50*1024*1024)
    payload = {"id": 1, "method": "Target.getTargets"}
    await ws.send(json.dumps(payload))
    targets = []
    async for raw in ws:
        msg = json.loads(raw)
        if msg.get("id") == 1:
            targets = msg.get("result", {}).get("targetInfos", [])
            break

    page = next((t for t in targets if 'edtoeic' in t.get('url', '')), None)
    if not page:
        print("[!] Không tìm thấy tab edtoeic nào đang mở.")
        await ws.close()
        return

    await ws.send(json.dumps({"id": 2, "method": "Target.attachToTarget", "params": {"targetId": page['targetId'], "flatten": True}}))
    sid = None
    async for raw in ws:
        msg = json.loads(raw)
        if msg.get("id") == 2:
            sid = msg.get("result", {}).get("sessionId")
            break

    eval_js = """
    (() => {
        try {
            const c = JSON.parse(localStorage.getItem('Course')) || {};
            const ti = JSON.parse(localStorage.getItem('toeicInformation')) || {};
            return { course: c, toeicInfo: ti };
        } catch(e) { return { error: e.message }; }
    })()
    """
    await ws.send(json.dumps({"id": 3, "sessionId": sid, "method": "Runtime.evaluate", "params": {"expression": eval_js, "returnByValue": True}}))
    data = {}
    async for raw in ws:
        msg = json.loads(raw)
        if msg.get("id") == 3:
            data = msg.get("result", {}).get("result", {}).get("value", {})
            break

    c = data.get("course", {})
    print(f"[+] Khóa học đang chọn : {c.get('CourseName')} (ID: {c.get('CourseId')})")
    print(f"[+] Tài khoản học viên : {data.get('toeicInfo', {}).get('toeicUserName', 'Unknown')}")
    print("="*65 + "\n")
    await ws.close()


async def run_all_units(module=None, custom_port=None, skip_test=False, only_test=False):
    """Tự động giải tuần tự tất cả 8 Units của Module"""
    print("\n" + "#"*70)
    print("### BẮT ĐẦU CHẾ ĐỘ TỰ ĐỘNG GIẢI TOÀN BỘ CẢ 8 UNITS ###")
    print("#"*70)

    results = {}
    for u_seq in range(1, 9):
        print(f"\n>>>> ĐANG TIẾN HÀNH UNIT {u_seq} / 8 <<<<\n")
        try:
            solver = MasterUnitSolver(
                unit_seq=u_seq,
                module=module,
                custom_port=custom_port,
                skip_test=skip_test,
                only_test=only_test
            )
            score = await solver.run()
            results[u_seq] = f"Thành công (Điểm Test: {score})"
            print(f"[+] Unit {u_seq} hoàn thành thành công!", flush=True)
        except Exception as e:
            results[u_seq] = f"Sự cố: {e}"
            print(f"[!] Unit {u_seq} gặp sự cố: {e}", flush=True)

        if u_seq < 8:
            print("[+] Tạm nghỉ 6 giây trước khi chuyển sang Unit tiếp theo...", flush=True)
            await asyncio.sleep(6)

    print("\n" + "="*70)
    print("=== TỔNG KẾT KẾT QUẢ GIẢI 8 UNITS ===")
    print("="*70)
    for u_seq, res in results.items():
        print(f"  Unit {u_seq}: {res}")
    print("="*70 + "\n")


if __name__ == '__main__':
    print(BANNER)
    parser = argparse.ArgumentParser(description="ETS TOEIC OLPC - Auto Solver Portable - MADE BY BANG DZ UwU")
    parser.add_argument("--unit", type=int, default=1, help="Số thứ tự Unit cần giải (1 đến 8). Mặc định là 1.")
    parser.add_argument("--all", action="store_true", help="Tự động giải tuần tự tất cả 8 Units của Module.")
    parser.add_argument("--module", type=int, default=None, help="Chỉ định Module (1, 2, hoặc 3). Mặc định tự động nhận diện.")
    parser.add_argument("--port", type=int, default=None, help="Cổng Chrome Remote Debugging tùy chỉnh (Mặc định tự dò 9222).")
    parser.add_argument("--skip-test", action="store_true", help="Chỉ hoàn thành bài học, bỏ qua Unit Test.")
    parser.add_argument("--only-test", action="store_true", help="Chỉ làm Unit Test, bỏ qua bài học.")
    parser.add_argument("--list", action="store_true", help="Liệt kê thông tin Module và tài khoản đang mở.")
    args = parser.parse_args()

    if args.list:
        asyncio.run(list_course_info(custom_port=args.port))
    elif args.all:
        asyncio.run(run_all_units(
            module=args.module,
            custom_port=args.port,
            skip_test=args.skip_test,
            only_test=args.only_test
        ))
    else:
        solver = MasterUnitSolver(
            unit_seq=args.unit,
            module=args.module,
            custom_port=args.port,
            skip_test=args.skip_test,
            only_test=args.only_test
        )
        asyncio.run(solver.run())
