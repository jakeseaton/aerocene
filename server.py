#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import time 

global seen 
seen = {} 

#Create custom HTTPRequestHandler class
class HTTPRequestHandler(BaseHTTPRequestHandler):
    
    #handle GET command
    def do_GET(self):
        
        try:
            #send code 200 response
            # self.send_error(404, 'file not found')
    
            print("client ip: " + self.client_address[0])

            if self.client_address[0] in seen:
                seen[self.client_address[0]] += 1 
            else:
                seen[self.client_address[0]] = 1 

            # simple rate limiting 
            if seen[self.client_address[0]] > 5: 
                print("too many requests")
                time.sleep(5)

            if seen[self.client_address[0]] > 8:
                self.send_error(404)

            # self.send_error(304)
            self.send_response(200)

            print seen

            return
            
        except IOError:
            print("error client ip: " + self.client_address[0])
            # self.send_error(404, 'file not found')
    
def run():
    print('http server is starting...')
    #ip and port of servr
    #by default http server port is 80
    server_address = ('10.252.15.135', 8080)

    httpd = HTTPServer(server_address, HTTPRequestHandler)

    print('http server is running...')

    httpd.serve_forever()
    
if __name__ == '__main__':
    run()
