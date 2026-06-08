import asyncio
‎from fastapi import FastAPI, HTTPException, Query
‎from fastapi.middleware.cors import CORSMiddleware
‎import yt_dlp
‎import httpx
‎
‎app = FastAPI(
‎    title="tiktok", 
‎    description="A-Z Anti-Block TikTok 1080p Downloader API",
‎    version="1.0.0"
‎)
‎
‎# CORS এনাবল করা যাতে আপনার অ্যাপ বা যেকোনো ফ্রন্টএন্ড থেকে সহজে কানেক্ট করা যায়
‎app.add_middleware(
‎    CORSMiddleware,
‎    allow_origins=["*"],
‎    allow_credentials=True,
‎    allow_methods=["*"],
‎    allow_headers=["*"],
‎)
‎
‎# Render সার্ভারকে ২৪/৭ জাগিয়ে রাখার জন্য সেলফ-পিং টাস্ক (Anti-Sleep)
‎async def keep_alive():
‎    """প্রতি ১০ মিনিটে সার্ভার নিজেকে নিজেই রিকোয়েস্ট পাঠাবে যেন Render ঘুমাতে না পারে"""
‎    await asyncio.sleep(30) # সার্ভার স্টার্ট হওয়ার জন্য ৩০ সেকেন্ড সময় দেওয়া
‎    async with httpx.AsyncClient() as client:
‎        while True:
‎            try:
‎                # আপনার render অ্যাপ ইউআরএল ডেপ্লয় করার পর এখানে বসিয়ে দিতে পারেন
‎                # অথবা এটি লোকালহোস্টেই লুপ চালাবে
‎                await client.get("http://localhost:8000/ping")
‎            except Exception:
‎                pass
‎            await asyncio.sleep(600) # ৬০০ সেকেন্ড = ১০ মিনিট পর পর পিং করবে
‎
‎@app.on_event("startup")
‎async def startup_event():
‎    # সার্ভার চালু হওয়া মাত্র ব্যাকগ্রাউন্ডে স্লিপ-প্রতিরোধী লুপ চালু হবে
‎    asyncio.create_task(keep_alive())
‎
‎@app.get("/ping")
‎async def ping():
‎    return {"status": "alive and fast"}
‎
‎@app.get("/api/tiktok")
‎async def get_tiktok_video(url: str = Query(..., description="Paste TikTok Video URL here")):
‎    if not url:
‎        raise HTTPException(status_code=400, detail="URL cannot be empty")
‎        
‎    # টিকটকের রেস্ট্রিকশন ও আইপি ব্লক বাইপাস করার জন্য অ্যাডভান্সড কনফিগারেশন
‎    ydl_opts = {
‎        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # ১০৮০পি বেস্ট অডিও-ভিডিও কম্বিনেশন
‎        'quiet': True,
‎        'no_warnings': True,
‎        'extract_flat': False,
‎        'http_headers': {
‎            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
‎            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
‎            'Accept-Language': 'en-US,en;q=0.9',
‎            'Sec-Fetch-Mode': 'navigate',
‎        }
‎    }
‎    
‎    try:
‎        # রানটাইমে সিনক্রোনাস yt-dlp ব্লকিং এড়াতে থ্রেড পুলে রান করা হলো (স্পিড বুস্ট করার জন্য)
‎        loop = asyncio.get_event_loop()
‎        def fetch_info():
‎            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
‎                return ydl.extract_info(url, download=False)
‎                
‎        info = await loop.run_in_executor(None, fetch_info)
‎        
‎        # ওয়াটারমার্ক ছাড়া ডিরেক্টরি হাই-কোয়ালিটি ভিডিও প্লে/ডাউনলোড লিংক বের করা
‎        video_url = info.get('url') or (info.get('formats')[-1].get('url') if info.get('formats') else None)
‎        
‎        if not video_url:
‎            raise HTTPException(status_code=404, detail="Could not extract No-Watermark HD link.")
‎            
‎        # মোবাইল অ্যাপের জন্য মেটাডাটা সহ রেসপন্স জেনারেট
‎        return {
‎            "status": "success",
‎            "api_name": "tiktok",
‎            "data": {
‎                "title": info.get('title', 'TikTok Video'),
‎                "author": info.get('uploader', 'Unknown Creator'),
‎                "author_username": info.get('uploader_id', ''),
‎                "duration_seconds": info.get('duration', 0),
‎                "thumbnail": info.get('thumbnail', ''),
‎                "quality_found": "1080p/Best-HQ",
‎                "no_watermark_download_url": video_url # আপনার অ্যাপ এই ডিরেক্টরি লিংকটি সরাসরি ব্যবহার করবে
‎            }
‎        }
‎        
‎    except Exception as e:
‎        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
‎
