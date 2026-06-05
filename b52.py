import asyncio
import httpx
from datetime import datetime
from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

# Cấu hình biến môi trường
PORT = int(os.getenv("PORT", 3002))
SELF_URL = os.getenv("SELF_URL", f"http://localhost:{PORT}")
API_TARGET_URL = 'https://jakpotgwab.geightdors.net/glms/v1/notify/taixiu?platform_id=b5&gid=vgmn_101'

# Trạng thái game
latest_result = {
    "Phien": 0,
    "Xuc_xac_1": 0,
    "Xuc_xac_2": 0,
    "Xuc_xac_3": 0,
    "Tong": 0,
    "Ket_qua": "",
    "id": "@thanhnhatx"
}

def update_result(d1, d2, d3, sid=None):
    global latest_result
    total = d1 + d2 + d3
    result = "Tài" if total > 10 else "Xỉu"
    
    latest_result = {
        "Phien": sid or latest_result["Phien"],
        "Xuc_xac_1": d1,
        "Xuc_xac_2": d2,
        "Xuc_xac_3": d3,
        "Tong": total,
        "Ket_qua": result,
        "id": "@thanhnhatx"
    }
    
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[🎲✅] Phiên {latest_result['Phien']} - {d1}-{d2}-{d3} ➜ Tổng: {total}, Kết quả: {result} | {time_str}")

async def fetch_game_data():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(API_TARGET_URL)
            data = response.json()
            
            if data.get("status") == "OK" and isinstance(data.get("data"), list) and len(data["data"]) > 0:
                game = data["data"][0]
                sid = game.get("sid")
                d1 = game.get("d1")
                d2 = game.get("d2")
                d3 = game.get("d3")
                
                if sid != latest_result["Phien"] and None not in (d1, d2, d3):
                    update_result(d1, d2, d3, sid)
        except Exception as e:
            print(f"❌ Lỗi khi lấy dữ liệu từ API GET: {e}")

async def background_tasks():
    # Loop fetch dữ liệu
    while True:
        await fetch_game_data()
        await asyncio.sleep(5)

async def keep_alive():
    # Loop giữ server không ngủ (tương đương setInterval 5 phút)
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(300)
            if "http" in SELF_URL:
                try:
                    await client.get(f"{SELF_URL}/api/b52")
                except:
                    pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_tasks())
    asyncio.create_task(keep_alive())

@app.get("/api/b52")
async def get_result():
    return latest_result

@app.get("/")
async def root():
    return {"status": "B52 Tài Xỉu đang chạy", "phien": latest_result["Phien"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)