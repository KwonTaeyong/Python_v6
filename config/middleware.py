from django.shortcuts import render, redirect, reverse
from django.http import Http404
import time
import datetime

class DisableBrowserCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response


class checkAuth:
    def __init__(self, get_response):
        self.get_response = get_response

    ## 개발 테스트용
    def test_auth(self):
        test_uuid = hex(int(time.time())).lower().replace("0x", "")
        ss_uuid = f"89d8d976-1d00-4d9c-8e0c-beca{test_uuid}"

        import random
        random_number = str(random.randint(1, 99)).zfill(4)

        ss_no = datetime.datetime.now().strftime("AS%Y%m%d") + random_number
        return redirect(reverse('imglist') + f"?ss_uuid={ss_uuid}&ss_no={ss_no}&ss_user=nowon")
    ##############

    def __call__(self, request):
        if 'robot' in request.path:
            response = self.get_response(request)
            return response
        if 'static' in request.path:
            response = self.get_response(request)
            return response
        if 'nowon' in request.path:
            return self.test_auth()

        if request.POST:
            req = request.POST
        else:
            req = request.GET

        ss_uuid = req.get('ss_uuid')

        time_delta = 0
        try:
            now_timestamp = int(time.time())

            hex_timestamp = ss_uuid[-8:]
            int_timestamp = int(hex_timestamp, 16)

            time_delta = abs(now_timestamp - int_timestamp)
        except:
            raise Http404('페이지를 찾을 수 없습니다.')
        if time_delta > 600:
            return render(request, 'auth_error.html')

        response = self.get_response(request)
        return response