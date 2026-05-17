# imagen ligera de node.js
FROM node:20-alpine

# el directorio de trabajo
WORKDIR /app

# se toma el archivos de dependencias y se instalan
COPY package*.json ./
RUN npm install

# se toma el codigo de el frontend
COPY . .

# puerto
EXPOSE 5173
