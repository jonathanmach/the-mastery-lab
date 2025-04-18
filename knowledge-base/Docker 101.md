
### Docker Volumes

There's 3 types of volumes in Docker:

1. **Named Volumes**: These are volumes that are created and managed by Docker and is not tied to any specific directory on the host machine unless explicitly configured. By default, Docker stores named volumes in a location managed by Docker itself.

```yaml
services:
  my-service:
    volumes:
      - my-volume:/path/in/container
volumes:
  my-volume:
```

2. **Bind Mounts**: These are volumes that are created and managed by the user. They are stored in a directory on the host machine.

```yaml
services:
  my-service:
    volumes:
      - /path/in/host:/path/in/container # ex: .data:/var/lib/postgresql/data
```

1. **Anonymous Volumes**: These are volumes that are created and managed by Docker. They are stored in a directory on the host machine.

```yaml
services:
  my-service:
    volumes:
      - /path/in/container
```

## Environment variables
To make your **Docker Compose** setup use environment variables from a .env file, just follow these steps:

1. Create a .env file in the same directory as docker-compose.yml:
```env
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydatabase
```
2. Update your docker-compose.yml to use the variables
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: postgres_container
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```