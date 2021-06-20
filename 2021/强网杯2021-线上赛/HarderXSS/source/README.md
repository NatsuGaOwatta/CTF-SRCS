### Startup

```bash
cd docker && docker build -t xxe_xss:1.50 .

docker run -it -P -d --add-host=feedback.cubestone.com:127.0.0.1 --add-host=flaaaaaaaag.cubestone.com:127.0.0.1 --add-host=cubestone.com:127.0.0.1  xxe_xss:1.50 flag{hardxss}

# or
docker-compose up -d --build
```

Source file copy from [QWB2021-HarderXSS](https://github.com/CrystalRays/QWB2021-HarderXSS), thanks @CrystalRays for open source.

