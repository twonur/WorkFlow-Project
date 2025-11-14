FROM nginx:1.25

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy our own configuration
COPY nginx.conf /etc/nginx/conf.d/nginx.conf 