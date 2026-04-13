#!/bin/bash

echo "=========================================="
echo "   DEMARRAGE DU SAAS BOT BUILDER (BASH)"
echo "=========================================="

echo "[1/3] Lancement de MongoDB via Docker..."
docker-compose up -d

echo "[2/3] Lancement du Backend (FastAPI)..."
cd backend && uvicorn main:app --reload &

echo "[3/3] Lancement du Frontend (React)..."
cd ../frontend && npm run dev &

echo "=========================================="
echo "   TOUT EST LANCE !"
echo "   Dashboard : http://localhost:5173"
echo "=========================================="
wait
