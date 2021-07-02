### Startup

```bash
docker build -t "tornado_ssti" .
docker run -dit -p "8123:8000" tornado_ssti

# or
docker-compose up -d --build
```

Source file copy from [qwb2021_tornado](https://gitee.com/b1ind/qwb2021_tornado), thanks @b1ind for open source.

