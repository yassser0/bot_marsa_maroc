# Étape 1 : Construction du Frontend (React/Vite)
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Étape 2 : Construction de l'image finale (Backend FastAPI + Frontend statique)
FROM python:3.10-slim
WORKDIR /app

# Copier les fichiers du backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

# Copier le frontend compilé depuis la première étape vers un dossier "dist" dans le backend
COPY --from=frontend-builder /app/frontend/dist ./dist

# Rendre le port 8001 accessible
EXPOSE 8001

# Démarrer le backend (qui servira aussi le frontend)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
