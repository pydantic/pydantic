from pydantic import AnyUrl, stricturl

url = AnyUrl.build(scheme='https', host='example.com', query='query=my query')
print(url)

my_url_builder = stricturl(quote_plus=True)
url = my_url_builder.build(scheme='https', host='example.com', query='query=my query')
print(url)
