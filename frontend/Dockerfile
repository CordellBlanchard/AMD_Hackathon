FROM node:20-alpine

WORKDIR /app

RUN npm config set strict-ssl false
RUN npm config set registry http://registry.npmjs.org/ 

# Copy the package.json and package-lock.json files to the working directory
COPY package*.json ./

# Remove any existing node_modules directory and package-lock.json file
RUN rm -rf node_modules package-lock.json


RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Build the Vite-React application
# RUN npm run build

# Expose port 80
EXPOSE 8080

# Start the server, change this to npm run serve for production
CMD ["npm", "run", "dev"]