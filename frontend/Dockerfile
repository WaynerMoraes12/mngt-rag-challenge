# Usa o Node.js para rodar o ambiente React/Vite
FROM node:20-alpine

WORKDIR /app

# Copia os arquivos de configuração e instala as dependências
COPY package*.json ./
RUN npm install

# Copia o resto do código da tela
COPY . .

# Expõe a porta do Vite
EXPOSE 5173

# O Vite precisa da flag --host para ficar acessível fora do contêiner
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]