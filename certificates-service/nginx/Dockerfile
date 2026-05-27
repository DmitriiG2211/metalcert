FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Create upload directory for static serving
RUN mkdir -p /app/uploads

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
