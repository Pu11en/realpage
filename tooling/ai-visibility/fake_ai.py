"""Fake OpenAI-style AI for free practice runs of tooling/ai-visibility/run.sh --practice."""
import json, http.server, random
ANS = ["For apartment property management, top options are Yardi Voyager, RealPage OneSite, Entrata and AppFolio. RealPage is strong for large portfolios. See https://www.realpage.com and https://www.yardi.com.",
       "I'd recommend Entrata or AppFolio for mid-size owners; Yardi Breeze for small ones. RealPage (realpage.com) is a property management software company known for revenue management.",
       "Best picks: 1. Yardi 2. Entrata 3. RealPage 4. Buildium. Source: https://www.capterra.com/property-management-software/"]
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get('content-length', 0)); req = self.rfile.read(n).decode()
        PROF = {"domain":"realpage.com","brandName":"RealPage","aliases":["RealPage Inc"],"category":"property management software","description":"RealPage sells property management and revenue software for apartment owners.","competitors":[{"name":"Yardi","domain":"yardi.com","relationship":"direct_competitor","confidence":0.9,"reason":"same buyer"},{"name":"Entrata","domain":"entrata.com","relationship":"direct_competitor","confidence":0.9,"reason":"same buyer"}],"promptSuggestions":[{"type":"category","topic":"pm software","prompt":"What is the best property management software for apartment owners?","auditCategory":"organic_discovery","targetIncluded":False},{"type":"brand","topic":"brand","prompt":"What does RealPage do?","auditCategory":"brand_awareness","targetIncluded":True}]}
        GEN = [{"type":"recommendation","topic":"pm","prompt":"Which software should a 500-unit apartment owner use?","targetIncluded":False,"auditCategory":"organic_discovery","keywordIds":[]},{"type":"brand","topic":"brand","prompt":"Is RealPage good for apartments?","targetIncluded":True,"auditCategory":"brand_awareness","keywordIds":[]}]
        if "Produce this JSON shape" in req: content = json.dumps(PROF)
        elif "Return only a valid JSON array" in req: content = json.dumps(GEN)
        elif "JSON" in req: content = "{}"
        else: content = random.choice(ANS)
        body = {"id":"x","object":"chat.completion","model":"mock","choices":[{"index":0,"message":{"role":"assistant","content":content},"finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":50,"total_tokens":60}}
        b = json.dumps(body).encode(); self.send_response(200); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(b))); self.end_headers(); self.wfile.write(b)
    do_GET = lambda self: (self.send_response(200), self.end_headers(), self.wfile.write(b'{"data":[]}'))
    def log_message(self,*a): pass
http.server.ThreadingHTTPServer(('127.0.0.1', int(__import__('sys').argv[1])), H).serve_forever()
