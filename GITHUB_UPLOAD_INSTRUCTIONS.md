# 🚀 คำสั่งสำหรับ Upload ไป GitHub

## ขั้นตอนที่ 1: สร้าง Repository บน GitHub
1. ไปที่ https://github.com
2. คลิก "New repository" (ปุ่มสีเขียว)
3. ใส่ข้อมูล:
   - Repository name: `enterprise-rag-chatbot`
   - Description: `🤖 AI-powered document search and chat system with RAG architecture`
   - เลือก Public หรือ Private
   - ❌ อย่าติ๊ก "Initialize this repository with..." อะไรเลย

## ขั้นตอนที่ 2: เชื่อมต่อและ Push (แทนที่ YOUR_USERNAME)

```bash
# เพิ่ม remote repository (แทนที่ YOUR_USERNAME ด้วยชื่อ GitHub ของคุณ)
git remote add origin https://github.com/YOUR_USERNAME/enterprise-rag-chatbot.git

# ตั้งชื่อ branch หลักเป็น main
git branch -M main

# Push ไฟล์ทั้งหมดขึ้น GitHub
git push -u origin main
```

## ขั้นตอนที่ 3: ตรวจสอบ Upload
- ไปดูที่ https://github.com/YOUR_USERNAME/enterprise-rag-chatbot
- ควรเห็นไฟล์และโครงสร้างทั้งหมด

## 📋 ไฟล์ที่จะถูก Upload:
- ✅ backend/ - RAG system components
- ✅ frontend/ - Streamlit UI components  
- ✅ config/ - Configuration management
- ✅ data/ - Storage directories (empty)
- ✅ tests/ - Test suite
- ✅ README.md - Project documentation
- ✅ requirements.txt - Dependencies
- ✅ docker-compose.yml - Docker setup
- ✅ .env.example - Configuration template

## 🔐 หมายเหตุความปลอดภัย:
- ✅ ไฟล์ .env (ที่มี API keys จริง) จะไม่ถูก upload เพราะอยู่ใน .gitignore
- ✅ เฉพาะ .env.example ที่เป็น template เท่านั้นที่จะขึ้น GitHub

ขอให้โชคดี! 🚀