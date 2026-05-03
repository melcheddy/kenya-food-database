def handler(request, response):
    response.status_code = 200
    response.headers['Content-Type'] = 'text/plain'
    response.write('Hello from pure Python on Vercel!')